import math
import time

from consoleLog import print_error
from scenario.base.filling_loop_signal import PRESSURE_INPUT_TYPE_RANGEABLE
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter


class FillingLoopAlarmScenario(Parent):
	PRESSURE_NORMAL = 3
	PRESSURE_LOW = 0
	MINIMUM_PRESSURE = 1.5
	PRESSURE_HYSTERESIS = 0.3
	AUTO_FILL_OFF = 0
	FILLING_DURATION = 5
	ALARM_TIMEOUT = 60
	CLEANUP_POLL_INTERVAL = 1

	def force_preset_load(self):
		return True

	def _read_parameter(self, program, program_type, parameter_id):
		parameter = RemoteControlParameter(
			programType=program_type, parameterId=parameter_id, programId=program.get_id(),
		)
		return parameter.get_value() if parameter.read() else None

	def _write_parameter(self, program, program_type, parameter_id, value):
		return RemoteControlParameter(
			programType=program_type, parameterId=parameter_id,
			programId=program.get_id(), parameterValue=value,
		).write()

	def _alarm_is(self, active):
		value = self._alarm.get_value()
		return value is not None and (value != self.RELAY_OFF) == active

	def _set_pressure(self, value):
		self._pressure.set_value(value, True)

	def _clear_alarm(self):
		self._set_pressure(self.PRESSURE_NORMAL)
		# Cleanup must also work after cancellation: wait_event() is interruptible.
		deadline = time.monotonic() + self.ALARM_TIMEOUT
		while not self._alarm_is(False):
			if time.monotonic() >= deadline:
				raise RuntimeError('авария подпитки не снялась при нормальном давлении')
			self.simple_wait(self.CLEANUP_POLL_INTERVAL)

	def _run_alarm_test(self, settings, sensors, outputs, sequence):
		self._status = 'FAIL'
		filling_loop = self._programList['filling_loop']
		self._pressure = filling_loop.getPressure()
		self._alarm = filling_loop.get_output_channel('alarm_output')
		sensors = [(self._pressure, self.PRESSURE_NORMAL), *sensors]
		channels = [sensor for sensor, _ in sensors] + [self._alarm, *outputs]
		if any(channel is None or not channel.is_mapped() for channel in channels):
			print_error('Не привязан обязательный датчик или выход аварийного сценария')
			return
		saved_sensors = [(sensor, sensor.get_value(), sensor.isManual()) for sensor, _ in sensors]
		if any(
			not isinstance(value, (int, float)) or not math.isfinite(value)
			or sensor.isShort() or sensor.isOpen()
			for sensor, value, _ in saved_sensors
		):
			print_error('Требуются исправные датчики с числовыми исходными значениями')
			return
		if saved_sensors[0][1] < self.PRESSURE_NORMAL:
			print_error('Исходное давление должно быть нормальным для безопасного восстановления')
			return

		parameter_type = snc.ProgramType.FILLING_LOOP
		parameter_id = snc.FillingLoopParameterId
		settings = [
			(filling_loop, parameter_type, parameter_id.AUTO_FILL, self.AUTO_FILL_OFF),
			(filling_loop, parameter_type, parameter_id.PRESSURE_INPUT_TYPE, PRESSURE_INPUT_TYPE_RANGEABLE),
			(filling_loop, parameter_type, parameter_id.MINIMUM_PRESSURE, self.MINIMUM_PRESSURE),
			(filling_loop, parameter_type, parameter_id.PRESSURE_HYST, self.PRESSURE_HYSTERESIS),
			(filling_loop, parameter_type, parameter_id.FILLING_DURATION, self.FILLING_DURATION),
			*settings,
		]
		saved = []
		for program, program_type, parameter_id, test_value in settings:
			value = self._read_parameter(program, program_type, parameter_id)
			if value is None:
				print_error(f'Не прочитан исходный параметр {program_type}/{parameter_id}')
				return
			saved.append((program, program_type, parameter_id, value, test_value))

		modified = []
		try:
			for sensor, value in sensors:
				# Do not register with set_sensor_value(): clear() must preserve restored manual modes.
				sensor.set_manual(True)
				sensor.set_value(value, True)
			for program, program_type, parameter_id, value, test_value in saved:
				modified.append((program, program_type, parameter_id, value))
				if not self._write_parameter(program, program_type, parameter_id, test_value):
					print_error(f'Не записан параметр {program_type}/{parameter_id}')
					return
			if sequence():
				self._status = 'OK'
		finally:
			try:
				self._clear_alarm()
			except Exception as error:
				self._status = 'FAIL'
				print_error(f'Не снята авария подпитки: {error}')
			for program, program_type, parameter_id, value in reversed(modified):
				try:
					if not self._write_parameter(program, program_type, parameter_id, value):
						raise RuntimeError('нет подтверждения записи')
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен параметр {program_type}/{parameter_id}: {error}')
			for sensor, value, manual in saved_sensors:
				try:
					try:
						sensor.set_value(value, True)
					finally:
						sensor.set_manual(manual)
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен датчик: {error}')
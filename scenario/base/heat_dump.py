"""Shared, boiler-free heat-extrication checklist setup and cleanup."""

import time

from consoleLog import print_error, print_log
from presets.list.heat_dump import CIRCUIT_ID, SOURCE_ID
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
from smartnet.cooling import send_cooling_request
from smartnet.message import CanListener
from smartnet.remoteControl import RemoteControlParameter


class HeatDumpFailed(Exception):
	pass


class RoomCoolingObserver:
	"""Diagnostics only: CAN backends need not echo a controller's outgoing frames."""

	def __init__(self, circuit_id):
		self.circuit_id = circuit_id
		self.observed = False

	def on_can_message_received(self, message):
		if (message.get_program_type() == snc.ProgramType.ROOM_DEVICE
			and message.getProgramId() == 0 and message.getFunctionId() == 1
			and message.getRequestFlag() == snc.RequestFlag.REQUEST
			and bytes(message.get_data() or ())[:2] == bytes((self.circuit_id, 1))):
			self.observed = True


class HeatDumpScenario(Parent):
	PUMP_TIMEOUT = 90
	ROOM_TIMEOUT = 120
	STABLE_DURATION = 5
	REPORT_INTERVAL = 10  # Firmware forgets an unrefreshed request after 30 seconds.
	ROOM_TEMPERATURE = 35
	ROOM_SETPOINT = 20

	def get_default_preset(self):
		return 'heat_dump'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'dhw': snc.ProgramType.DHW,
			'snow': snc.ProgramType.SNOWMELT,
			'pool': snc.ProgramType.POOL,
			'circuit': snc.ProgramType.HEATING_CIRCUIT,
			'room_1': snc.ProgramType.ROOM_DEVICE,
			'room_2': snc.ProgramType.ROOM_DEVICE,
		}

	def setting(self, key, program_type, parameter_id, value, index=None):
		return (self._programList[key], program_type, parameter_id, value, index)

	def consumer_settings(self, key):
		return [
			self.setting(key, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID, SOURCE_ID),
			self.setting(key, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.HEAT_EXTRICATION_ENABLED, 1),
		]

	def circuit_settings(self):
		return self.consumer_settings('circuit') + [
			# PUMP_MODE_ALWAYS_OFF: the cooling request must override this mode.
			self.setting('circuit', snc.ProgramType.HEATING_CIRCUIT,
				snc.HeatingCircuitParameterId.PUMP_MODE, 4),
		]

	def room_settings(self, key, slot, allowed):
		room = snc.RoomDeviceParameterId
		return [
			self.setting(key, snc.ProgramType.ROOM_DEVICE, room.WORK_MODE, snc.RoomWorkMode.COMFORT),
			self.setting(key, snc.ProgramType.ROOM_DEVICE, room.ROOM_COMFORT_TEMPERATURE, self.ROOM_SETPOINT),
			self.setting(key, snc.ProgramType.ROOM_DEVICE, room.HEAT_EXTRICATION, int(allowed), slot),
		]

	def _parameter(self, program, program_type, parameter_id, value=None, index=None):
		return RemoteControlParameter(programType=program_type, parameterId=parameter_id,
			programId=program.get_id(), parameterValue=value, parameterIndex=index)

	def _read(self, program, program_type, parameter_id, index=None):
		parameter = self._parameter(program, program_type, parameter_id, index=index)
		value = parameter.get_value() if parameter.read() else None
		if value is None:
			raise HeatDumpFailed(f'Не прочитан параметр {program.get_id()}/{program_type}/{parameter_id}/{index}')
		return value

	def _put(self, program, program_type, parameter_id, value, index=None):
		parameter = self._parameter(program, program_type, parameter_id, value, index)
		if not parameter.write():
			raise HeatDumpFailed(f'Не записан параметр {program.get_id()}/{program_type}/{parameter_id}/{index}')
		if self._read(program, program_type, parameter_id, index) != value:
			raise HeatDumpFailed(f'Не подтверждён параметр {program.get_id()}/{program_type}/{parameter_id}/{index}')

	def _cooling(self, enabled):
		# Mark active before sending, so even a failed transmission is cancelled in finally.
		self._cooling_active = enabled
		send_cooling_request(SOURCE_ID, enabled)
		self._last_report = time.monotonic()

	def wait(self, delay):
		# All scenario waits pass through here; never let the 30 s firmware TTL expire.
		if not getattr(self, '_cooling_active', False):
			return super().wait(delay)
		deadline = time.monotonic() + delay
		while time.monotonic() < deadline:
			if time.monotonic() - self._last_report >= self.REPORT_INTERVAL:
				self._cooling(True)
			super().wait(min(1, max(0, deadline - time.monotonic())))
		return True

	def expect(self, channel, expected, label, timeout=None):
		if not channel.is_mapped():
			raise HeatDumpFailed(f'Не назначен выход: {label}')
		if timeout is None:
			timeout = self.PUMP_TIMEOUT
		def matches():
			state = channel.get_value()
			return state is not None and (expected(state) if callable(expected) else state == expected)
		if not self.wait_state_permanence(matches, self.STABLE_DURATION, timeout):
			raise HeatDumpFailed(f'Выход {label}: неверное состояние ({channel.get_value()})')
		print_log(f'{label}: ожидаемое состояние подтверждено')

	def run_heat_dump(self, settings, sensors, baseline, active, observe_rooms=False):
		self._status = 'FAIL'
		self._cooling_active = False
		observer = None
		try:
			saved = [(p, t, i, self._read(p, t, i, index), index)
				for p, t, i, _, index in settings]
			saved_sensors = []
			for channel, value in sensors:
				if not channel.is_mapped():
					raise HeatDumpFailed('Не назначен необходимый датчик')
				saved_sensors.append((channel, channel.get_value(), channel.isManual()))
		except (HeatDumpFailed, KeyError) as error:
			print_error(str(error))
			return

		try:
			for channel, value in sensors:
				channel.set_manual(True)
				channel.set_value(value, True)
			for setting in settings:
				self._put(*setting)
			# Cancel a stale request left by an interrupted earlier run.
			self._cooling(False)
			baseline()
			if observe_rooms:
				observer = RoomCoolingObserver(CIRCUIT_ID)
				CanListener.subscribe(observer)
			print_log('Виртуальный источник отправляет запрос на сброс тепла')
			self._cooling(True)
			active()
			if observer is not None:
				print_log('CAN-запрос контура комнатам: ' +
					('наблюдался' if observer.observed else 'не наблюдался (проверены клапаны)'))
			self._status = 'OK'
		except HeatDumpFailed as error:
			print_error(str(error))
		finally:
			if observer is not None:
				CanListener.unsubscribe(observer)
			try:
				self._cooling(False)
			except Exception as error:
				self._status = 'FAIL'
				print_error(f'Не отменён сигнал охлаждения: {error}')
			for program, program_type, parameter_id, value, index in reversed(saved):
				try:
					self._put(program, program_type, parameter_id, value, index)
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен параметр {parameter_id}/{index}: {error}')
			for channel, value, manual in saved_sensors:
				try:
					try:
						if value is not None:
							channel.set_value(value, True)
					finally:
						channel.set_manual(manual)
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен датчик: {error}')

	def clear(self):
		if getattr(self, '_cooling_active', False):
			try:
				self._cooling(False)
			except Exception as error:
				self._status = 'FAIL'
				print_error(f'Не отменён сигнал охлаждения: {error}')
		super().clear()
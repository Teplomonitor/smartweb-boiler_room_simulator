"""Shared setup and cleanup for double-pump controller scenarios."""

import time

from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc


class DoublePumpScenario(Parent):
	STATE_TIMEOUT = 30
	STABLE_DURATION = 3
	INPUT_SETTLE_DURATION = 6
	CLEANUP_POLL_INTERVAL = 1
	PUMP_HEALTHY = 0
	PUMP_FAULT = 1
	SETTINGS = ('double_power', 'training_enabled', 'manual_mode_enabled')

	def get_required_programs(self):
		return {'double_pump': snc.ProgramType.DOUBLE_PUMP}

	def get_default_preset(self):
		return 'double_pump_discrete'

	def _set_input(self, name, value):
		sensor = self._pump.get_input_channel(name)
		sensor.set_manual(True)
		sensor.set_value(value, True)

	def _pump_states(self):
		states = []
		for outputs in self._pump_outputs:
			values = [self._pump.read_output(channel) for channel in outputs]
			if any(value is None for value in values):
				return None
			states.append(any(value > self.RELAY_OFF for value in values))
		return states

	def pumps_are_off(self):
		return self._pump_states() == [False, False]

	def one_pump_is_on(self):
		states = self._pump_states()
		return states is not None and sum(states) == 1

	def _alarm_is(self, active):
		value = self._pump.read_output(self._alarm)
		return value is not None and (value > self.RELAY_OFF) == active

	def _healthy_and_off(self):
		return (
			self._pump.read_parameter_value('alarm_status') == self.PUMP_HEALTHY
			and self._alarm_is(False) and self.pumps_are_off()
		)

	def both_pumps_failed_and_off(self):
		return (
			self._pump.read_parameter_value('pump_1_status') == self.PUMP_FAULT
			and self._pump.read_parameter_value('pump_2_status') == self.PUMP_FAULT
			and self._alarm_is(True) and self.pumps_are_off()
		)

	def check_state(self, predicate, description):
		print_log(description)
		if self.wait_state_permanence(predicate, self.STABLE_DURATION, self.STATE_TIMEOUT):
			return True
		print_error(f'Не выполнено: {description}')
		return False

	def _clear_test_faults(self):
		for name in ('control', 'pump_1_error', 'pump_2_error'):
			self._set_input(name, 'open')
		# Do not use interruptible scenario waits during cancellation cleanup.
		self.simple_wait(self.INPUT_SETTLE_DURATION)
		if not self._pump.write_parameter('alarm_status', self.PUMP_HEALTHY):
			raise RuntimeError('не подтверждён сброс неисправности насосов')
		deadline = time.monotonic() + self.STATE_TIMEOUT
		while not self._healthy_and_off():
			if time.monotonic() >= deadline:
				raise RuntimeError('не снята авария или насосы не остановились')
			self.simple_wait(self.CLEANUP_POLL_INTERVAL)

	def run_pump_test(self, sequence):
		self._status = 'FAIL'
		self._pump = self._programList['double_pump']
		self._pump_outputs = [
			[channel for channel in (
				self._pump.get_output_channel(f'discrete_pump_{index}'),
				self._pump.get_output_channel(f'analog_pump_{index}'),
			) if channel.is_mapped()]
			for index in (1, 2)
		]
		self._alarm = self._pump.get_output_channel('alarm')
		sensors = list(self._pump.get_inputs().values())
		if (any(not outputs for outputs in self._pump_outputs)
				or not self._alarm.is_mapped()
				or any(not sensor.is_mapped() for sensor in sensors)):
			print_error('Требуются входы управления, протока, двух аварий и выходы обоих насосов и аварии')
			return
		saved_sensors = [
			(sensor, sensor.get_value(), sensor.isManual(), sensor.isOpen(), sensor.isShort())
			for sensor in sensors
		]
		if any(value is None for _, value, _, _, _ in saved_sensors):
			print_error('Неизвестны исходные значения входов')
			return
		if (any(self._pump.get_input_channel(name).isShort()
				for name in ('pump_1_error', 'pump_2_error'))
				or self._pump.read_parameter_value('alarm_status') != self.PUMP_HEALTHY):
			print_error('Перед тестом необходимо снять и сбросить исходные аварии насосов')
			return
		saved_settings = []
		for name in self.SETTINGS:
			value = self._pump.read_parameter_value(name)
			if value is None:
				print_error(f'Не прочитан параметр {name}')
				return
			saved_settings.append((name, value))

		modified = []
		try:
			for name in ('control', 'pump_1_error', 'pump_2_error'):
				self._set_input(name, 'open')
			# Flow is produced by simulator.double_pump from the actual controller outputs.
			self._pump.get_input_channel('flow').set_manual(False)
			for name, value in saved_settings:
				modified.append((name, value))
				if not self._pump.write_parameter(name, 0):
					print_error(f'Не записан параметр {name}')
					return
			self.wait(self.INPUT_SETTLE_DURATION)
			if not self._pump.write_parameter('alarm_status', self.PUMP_HEALTHY):
				print_error('Не подтверждён сброс неисправности насосов')
				return
			if not self.check_state(self._healthy_and_off, 'Исходно оба насоса выключены, аварий нет'):
				return
			if sequence():
				self._status = 'OK'
		finally:
			try:
				self._clear_test_faults()
			except Exception as error:
				self._status = 'FAIL'
				print_error(f'Ошибка снятия тестовой аварии: {error}')
			for sensor, value, manual, was_open, was_short in saved_sensors:
				try:
					try:
						sensor.set_value(value, True)
						if was_open or was_short:
							sensor.set_value('open' if was_open else 'short', True)
					finally:
						sensor.set_manual(manual)
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен вход {sensor.get_title()}: {error}')
			for name, value in reversed(modified):
				try:
					if not self._pump.write_parameter(name, value):
						raise RuntimeError('нет подтверждения записи')
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен параметр {name}: {error}')
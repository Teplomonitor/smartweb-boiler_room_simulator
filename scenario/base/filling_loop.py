from consoleLog import print_error
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc

from scenario.base.filling_loop_signal import (
	PRESSURE_INPUT_TYPE_OPENABLE,
	PRESSURE_INPUT_TYPE_RANGEABLE,
	PRESSURE_INPUT_TYPE_SHORTABLE,
	read_pressure_input_type,
	write_pressure_input_type,
)


class FillingLoopScenario(Parent):
	PRESSURE_SENSOR_MIN = 0
	PRESSURE_SENSOR_MAX = 10
	RANGE_PRESSURE_MARGIN = 0.1
	DEFAULT_FILLING_DURATION = 20
	OUTPUT_FILLING = 'filling_loop_output'
	OUTPUT_ALARM = 'alarm_output'
	PRESSURE_INPUT_TYPE = PRESSURE_INPUT_TYPE_SHORTABLE

	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		self._filling_loop = self._programList['fillingLoop']
		self._original_pressure_input_type = None
		self._test_pressure_input_type = None

	def get_required_programs(self):
		return {'fillingLoop': snc.ProgramType.FILLING_LOOP}

	def get_default_preset(self):
		return 'filling_loop'

	def force_preset_load(self):
		return True

	def read_parameter(self, parameter):
		return self._filling_loop.read_parameter_value(parameter)

	def write_parameter(self, parameter, value):
		return self._filling_loop.write_parameter(parameter, value)

	def read_filling_duration(self):
		return self.read_parameter('fillingDuration')

	def read_counter(self):
		return self.read_parameter('autoFillCounter')

	def get_filling_output(self):
		return self._filling_loop.get_output_channel(self.OUTPUT_FILLING)

	def get_alarm_output(self):
		return self._filling_loop.get_output_channel(self.OUTPUT_ALARM)

	def filling_is_on(self):
		return self.get_filling_output().get_value() != self.RELAY_OFF

	def filling_is_off(self):
		return not self.filling_is_on()

	def alarm_is_on(self):
		return self.get_alarm_output().get_value() != self.RELAY_OFF

	def alarm_is_off(self):
		return not self.alarm_is_on()

	def set_pressure(self, value):
		self.set_sensor_value(self._filling_loop.getPressure(), value)

	def get_pressure_input_type(self):
		if self._test_pressure_input_type is not None:
			return self._test_pressure_input_type
		return self.PRESSURE_INPUT_TYPE

	def read_range_pressure(self, low_pressure):
		minimum_pressure = self.read_parameter('minimumPressure')
		pressure_hyst = self.read_parameter('pressureHyst')
		if minimum_pressure is None or pressure_hyst is None:
			return None

		try:
			minimum_pressure = float(minimum_pressure)
			pressure_hyst = float(pressure_hyst)
		except (TypeError, ValueError):
			return None

		if pressure_hyst < 0:
			return None
		margin = self.RANGE_PRESSURE_MARGIN
		if low_pressure:
			value = minimum_pressure - pressure_hyst - margin
		else:
			value = minimum_pressure + margin
		if not self.PRESSURE_SENSOR_MIN <= value <= self.PRESSURE_SENSOR_MAX:
			return None
		return value

	def set_normal_pressure(self):
		input_type = self.get_pressure_input_type()
		if input_type == PRESSURE_INPUT_TYPE_SHORTABLE:
			value = 'open'
		elif input_type == PRESSURE_INPUT_TYPE_OPENABLE:
			value = 'short'
		elif input_type == PRESSURE_INPUT_TYPE_RANGEABLE:
			value = self.read_range_pressure(False)
			if value is None:
				return False
		else:
			return False
		self.set_pressure(value)
		return True

	def set_low_pressure(self):
		input_type = self.get_pressure_input_type()
		if input_type == PRESSURE_INPUT_TYPE_SHORTABLE:
			value = 'short'
		elif input_type == PRESSURE_INPUT_TYPE_OPENABLE:
			value = 'open'
		elif input_type == PRESSURE_INPUT_TYPE_RANGEABLE:
			value = self.read_range_pressure(True)
			if value is None:
				return False
		else:
			return False
		self.set_pressure(value)
		return True

	def prepare_pressure_input_type(self, input_type=None):
		if input_type is None:
			input_type = self.PRESSURE_INPUT_TYPE
		if self._original_pressure_input_type is None:
			self._original_pressure_input_type = read_pressure_input_type(self._filling_loop)
		if self._original_pressure_input_type is None:
			return False
		if not write_pressure_input_type(self._filling_loop, input_type):
			return False
		self._test_pressure_input_type = input_type
		return True

	def reset_test_state(self):
		if not self.write_parameter('autoFill', 0):
			return False
		if not self.write_parameter('singleFill', 0):
			return False
		if not self.write_parameter('autoFillCounter', 0):
			return False
		if not self.write_parameter('pressureLossAlarmReset', 0):
			return False
		if not self.set_normal_pressure():
			return False
		return self.wait_state_permanence(self.filling_is_off, 2, 30)

	def prepare_low_pressure_test(self, auto_fill=True):
		if not self.prepare_pressure_input_type():
			return False
		if not self.reset_test_state():
			return False
		if auto_fill and not self.write_parameter('autoFill', 1):
			return False
		return self.set_low_pressure()

	def finish_test(self, original_duration=None):
		for parameter in ('singleFill', 'autoFill', 'pressureLossAlarmReset', 'autoFillCounter'):
			if not self.write_parameter(parameter, 0):
				print_error(f'Не удалось сбросить параметр подпитки {parameter}')
				self._status = 'FAIL'
		if original_duration is not None:
			if not self.write_parameter('fillingDuration', original_duration):
				print_error('Не удалось восстановить время подпитки')
				self._status = 'FAIL'
		if self._original_pressure_input_type is not None:
			if not write_pressure_input_type(self._filling_loop, self._original_pressure_input_type):
				print_error('Не удалось восстановить тип сигнала давления подпитки')
				self._status = 'FAIL'
			self._test_pressure_input_type = self._original_pressure_input_type
			self._original_pressure_input_type = None
		if not self.set_normal_pressure():
			print_error('Не удалось восстановить нормальное давление подпитки')
			self._status = 'FAIL'
		self._test_pressure_input_type = None

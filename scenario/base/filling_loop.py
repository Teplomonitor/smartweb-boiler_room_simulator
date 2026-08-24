from scenario.scenario import Scenario as Parent
import smartnet.constants as snc


class FillingLoopScenario(Parent):
	NORMAL_PRESSURE = 'short'
	LOW_PRESSURE = 'open'
	DEFAULT_FILLING_DURATION = 20
	OUTPUT_FILLING = 'filling_loop_output'
	OUTPUT_ALARM = 'alarm_output'

	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		self._filling_loop = self._programList['fillingLoop']

	def get_required_programs(self):
		return {'fillingLoop': snc.ProgramType.FILLING_LOOP}

	def get_default_preset(self):
		return 'filling_loop'

	def force_preset_load(self):
		return True

	def read_parameter(self, parameter):
		return self._filling_loop.read_parameter_value(parameter)

	def write_parameter(self, parameter, value):
		result = self._filling_loop.write_parameter_value(parameter, value)
		return result is not None

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

	def set_normal_pressure(self):
		self.set_pressure(self.NORMAL_PRESSURE)

	def set_low_pressure(self):
		self.set_pressure(self.LOW_PRESSURE)

	def reset_test_state(self):
		if not self.write_parameter('autoFill', 0):
			return False
		if not self.write_parameter('singleFill', 0):
			return False
		if not self.write_parameter('autoFillCounter', 0):
			return False
		if not self.write_parameter('pressureLossAlarmReset', 0):
			return False
		self.set_normal_pressure()
		return self.wait_state_permanence(self.filling_is_off, 2, 30)

	def prepare_low_pressure_test(self, auto_fill=True):
		if not self.reset_test_state():
			return False
		if auto_fill and not self.write_parameter('autoFill', 1):
			return False
		self.set_low_pressure()
		return True

	def finish_test(self, original_duration=None):
		self.write_parameter('singleFill', 0)
		self.write_parameter('autoFill', 0)
		self.write_parameter('pressureLossAlarmReset', 0)
		self.write_parameter('autoFillCounter', 0)
		if original_duration is not None:
			self.write_parameter('fillingDuration', original_duration)
		self.set_normal_pressure()

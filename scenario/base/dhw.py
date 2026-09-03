import smartnet.constants as snc

from scenario.scenario import Scenario as Parent


class DhwScenario(Parent):
	MODE_COMFORT = 0
	MODE_ECONOM = 1
	MODE_PROGRAM = 2
	MODE_OFF = 3

	CIRCULATION_ON = 0
	CIRCULATION_PROGRAM = 1
	CIRCULATION_PERIOD = 2
	CIRCULATION_OFF = 3

	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		self._dhw = self._programList['dhw']

		self._filling_loop = self._programList.get('filling_loop')

	def get_required_programs(self):
		return {
			'dhw': snc.ProgramType.DHW,
		}

	def get_default_preset(self):
		return 'dhw'

	def read_parameter(self, name, index=None):
		return self._dhw.read_parameter_value(name, index=index)

	def write_parameter(self, name, value, index=None):
		return self._dhw.write_parameter_value(name, value, index=index)

	def get_supply_pump_state(self):
		return self._dhw.get_supply_pump_state().get_value()

	def get_circulation_pump_state(self):
		return self._dhw.get_circulation_pump_state().get_value()

	def supply_pump_is_on(self):
		return self.get_supply_pump_state() != self.RELAY_OFF

	def supply_pump_is_off(self):
		return not self.supply_pump_is_on()

	def circulation_pump_is_on(self):
		return self.get_circulation_pump_state() != self.RELAY_OFF

	def circulation_pump_is_off(self):
		return not self.circulation_pump_is_on()

	def pumps_are_on(self):
		return self.supply_pump_is_on() and self.circulation_pump_is_on()

	def pumps_are_off(self):
		return self.supply_pump_is_off() and self.circulation_pump_is_off()

	def set_boiler_temperature(self, value):
		self.set_sensor_value(self._dhw.get_temperature(), value)

	def set_pressure(self, value):
		if self._filling_loop is None:
			return False
		self.set_sensor_value(self._filling_loop.getPressure(), value)
		return True

	def read_required_temperature(self):
		return self.read_parameter('temperatureDesired')

	def set_circulation_mode(self, mode):
		return self.write_parameter('circulationMode', mode)

	def wait_for_pump_state(self, predicate, timeout=60):
		return self.wait_event(predicate, timeout)

from scenario.scenario import Scenario as Parent
import smartnet.constants as snc


class PoolScenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		self._pool = self._programList['pool']

	def get_required_programs(self):
		return {
			'pool': snc.ProgramType.POOL,
		}

	def get_default_preset(self):
		return 'swimmingPool'

	def read_required_pool_temperature(self):
		return self._pool.read_parameter_value('currentRequiredPoolTemperature')

	def get_loading_pump_state(self):
		return self._pool.getLoadingPumpState().get_value()

	def loading_pump_is_on(self):
		return self.get_loading_pump_state() != self.RELAY_OFF

	def loading_pump_is_off(self):
		return not self.loading_pump_is_on()

	def get_circulation_pump_state(self):
		return self._pool.getCirculationPumpState().get_value()

	def circulation_pump_is_on(self):
		return self.get_circulation_pump_state() != self.RELAY_OFF

	def circulation_pump_is_off(self):
		return not self.circulation_pump_is_on()

	def set_pool_temperature(self, value):
		self.set_sensor_value(self._pool.get_temperature(), value)

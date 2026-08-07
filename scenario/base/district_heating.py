from scenario.scenario import Scenario as Parent
import smartnet.constants as snc


class DistrictHeatingScenario(Parent):
	BACKWARD_CONTROL_TYPE_CONST = 0
	BACKWARD_TEMPERATURE_TOLERANCE = 2

	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		self._district_heating = self._programList['districtHeating']

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
		}

	def get_default_preset(self):
		return 'district_heating'

	def read_backward_control_type(self):
		return self._district_heating.read_parameter_value('backwardControlType')

	def read_maximum_backward_temperature(self):
		return self._district_heating.read_parameter_value('maximumBackwardTemperature')

	def read_current_maximum_backward_temperature(self):
		return self._district_heating.read_parameter_value('currentMaximumBackwardTemperature')

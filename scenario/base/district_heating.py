from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
import smartnet.remoteControl as sr
import smartnet.units as snu


class DistrictHeatingScenario(Parent):
	BACKWARD_CONTROL_TYPE_CONST = 0
	BACKWARD_CONTROL_TYPE_AUTO = 1
	BACKWARD_TEMPERATURE_TOLERANCE = 2

	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		self._district_heating = self._programList['districtHeating']
		# Not every district heating scenario needs an outdoor sensor (e.g. the
		# 3.12.10.x reserve generator family uses DHW as its consumer, which does
		# not depend on outdoor temperature), so this is optional.
		self._outdoor = self._programList.get('outdoor')

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'outdoor': snc.ProgramType.OUTDOOR_SENSOR,
		}

	def get_default_preset(self):
		return 'district_heating'

	def read_backward_control_type(self):
		return self._district_heating.read_parameter_value('backwardControlType')
	
	def write_backward_control_type(self, value):
		return self._district_heating.write_parameter_value('backwardControlType', value)

	def read_maximum_backward_temperature(self):
		return self._district_heating.read_parameter_value('maximumBackwardTemperature')

	def read_current_maximum_backward_temperature(self):
		return self._district_heating.read_parameter_value('currentMaximumBackwardTemperature')

	def read_maximum_backward_temperature_ii(self):
		return self._district_heating.read_parameter_value('maximumBackwardTemperatureII')

	def read_outdoor_temperature_ii(self):
		return self._district_heating.read_parameter_value('outdoorTemperatureII')

	def get_outdoor_temperature(self):
		return self._outdoor.getOutdoorTemperature().get_value()

	def set_outdoor_temperature(self, value):
		self.set_sensor_value(self._outdoor.getOutdoorTemperature(), value)
		
	def write_valve_running_time(self, value):
		return self._district_heating.write_parameter_value('valveRunningTime', value)

	def read_valve_running_time(self):
		return self._district_heating.read_parameter_value('valveRunningTime')

	def read_temperature_source_power_request_delay(self):
		return self._district_heating.read_parameter_value('temperatureSourcePowerRequestDelay')

	def write_temperature_source_power_request_delay(self, value):
		return self._district_heating.write_parameter_value('temperatureSourcePowerRequestDelay', value)

	def read_temperature_source_required_temperature(self, program):
		'''
		Reads TemperatureSourceParameterId.REQUIRED_TEMPERATURE for a backup/reserve
		heat generator program (e.g. the BOILER referenced by
		DistrictHeatingParameterId.PARAM_TEMPERATURE_SOURCE_ID).
		'''
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.TEMPERATURE_SOURCE,
			parameterId=snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE,
			programId=program.get_id(),
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def read_temperature_source_consumer_id(self, program):
		'''
		Reads TemperatureSourceParameterId.CURRENTLY_SERVICES_CONSUMER_ID for a
		backup/reserve heat generator program.
		'''
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.TEMPERATURE_SOURCE,
			parameterId=snc.TemperatureSourceParameterId.CURRENTLY_SERVICES_CONSUMER_ID,
			programId=program.get_id(),
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def read_temperature_generator_parameter(self, program, parameter_id):
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.TEMPERATURE_GENERATOR,
			parameterId=parameter_id,
			programId=program.get_id(),
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def write_temperature_generator_parameter(self, program, parameter_id, value):
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.TEMPERATURE_GENERATOR,
			parameterId=parameter_id,
			parameterValue=value,
			programId=program.get_id(),
		)
		return parameter.write()

	def read_circuit_parameter(self, circuit, parameter):
		return circuit.read_parameter_value(parameter)

	def write_circuit_parameter(self, circuit, parameter, value):
		return circuit.write_parameter_value(parameter, value)

	def read_circuit_heat_calculation_mode(self, circuit):
		return self.read_circuit_parameter(circuit, 'heatCalculationMode')

	def write_circuit_heat_calculation_mode(self, circuit, value):
		return self.write_circuit_parameter(circuit, 'heatCalculationMode', value)

	def read_circuit_required_constant_flow_temperature(self, circuit):
		return self.read_circuit_parameter(circuit, 'requiredConstantFlowTemperature')

	def write_circuit_required_constant_flow_temperature(self, circuit, value):
		return self.write_circuit_parameter(circuit, 'requiredConstantFlowTemperature', value)

	def read_circuit_temperature_compensation(self, circuit):
		return self.read_circuit_parameter(circuit, 'temperatureCompensation')

	def write_circuit_temperature_compensation(self, circuit, value):
		return self.write_circuit_parameter(circuit, 'temperatureCompensation', value)

	def backup_generator_is_requested(self, program):
		'''
		True if the district heating program currently requires heat from the
		given backup/reserve generator program: its required temperature is
		above zero and it currently services the district heating program.
		'''
		required_temperature = self.read_temperature_source_required_temperature(program)
		consumer_id = self.read_temperature_source_consumer_id(program)

		if required_temperature is None or consumer_id is None:
			return None

		return (
			required_temperature not in (0, snu.SENSOR_UNDEFINED)
			and consumer_id == self._district_heating.get_id()
		)

	def backup_generator_is_not_requested(self, program):
		'''
		True if the backup/reserve generator's required temperature is 0 or
		SENSOR_UNDEFINED, meaning district heating does not request heat from it.
		'''
		required_temperature = self.read_temperature_source_required_temperature(program)

		if required_temperature is None:
			return None

		return required_temperature in (0, snu.SENSOR_UNDEFINED)

	def wait_backup_generator_requested(self, program, stabilization_duration, timeout):
		return self.wait_state_permanence(
			lambda: self.backup_generator_is_requested(program) is True,
			stabilization_duration,
			timeout,
		)

	def wait_backup_generator_not_requested(self, program, stabilization_duration, timeout):
		return self.wait_state_permanence(
			lambda: self.backup_generator_is_not_requested(program) is True,
			stabilization_duration,
			timeout,
		)

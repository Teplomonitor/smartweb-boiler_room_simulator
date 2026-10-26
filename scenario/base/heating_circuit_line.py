from consoleLog import print_error
from scenario.base.cascade_manager import CascadeManagerScenario
import smartnet.constants as snc


class HeatingCircuitLineScenario(CascadeManagerScenario):
	PUMP_ALWAYS_ON = 2
	PUMP_ALWAYS_OFF = 3
	DHW_COMFORT = 0
	DHW_OFF = 3
	OUTDOOR_TEMPERATURE = 15
	SENSOR_TEMPERATURE = 30
	MINIMUM_FLOW = 5
	LINE_BASE_SETPOINT = 10
	MAXIMUM_FLOW = 90
	CIRCUIT_REQUESTS = (40, 50)
	DHW_REQUEST = 55
	# Consumer overrun, selector reset (20 + 20 s), line overrun and CAN delays.
	CONSUMER_TIMEOUT = 180
	LINE_TIMEOUT = 180
	OBSERVATION_DURATION = 120

	def get_default_preset(self):
		return 'heating_circuit_3_3_6'

	def get_required_programs(self):
		return {
			'heating_line': snc.ProgramType.HEATING_CIRCUIT,
			'heating_circuit_1': snc.ProgramType.HEATING_CIRCUIT,
			'heating_circuit_2': snc.ProgramType.HEATING_CIRCUIT,
			'dhw': snc.ProgramType.DHW,
			'cascade': snc.ProgramType.CASCADE_MANAGER,
			'boiler_1': snc.ProgramType.BOILER,
			'boiler_2': snc.ProgramType.BOILER,
			'outdoor': snc.ProgramType.OUTDOOR_SENSOR,
		}

	def _circuits(self):
		return [self._programList[f'heating_circuit_{index}'] for index in (1, 2)]

	def _settings(self):
		settings = []
		for name, program in self._programList.items():
			if name == 'outdoor':
				continue
			settings.extend([
				(program, snc.ProgramType.PROGRAM, snc.ProgramParameterId.TRAINING_ENABLED, 0),
				(program, snc.ProgramType.PROGRAM, snc.ProgramParameterId.MANUAL_MODE_ENABLED, 0),
			])
		line = self._programList['heating_line']
		for circuit, request in zip([line, *self._circuits()], [self.LINE_BASE_SETPOINT, *self.CIRCUIT_REQUESTS]):
			settings.extend([
				(circuit, snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.PUMP_MODE, self.PUMP_ALWAYS_OFF),
				(circuit, snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.FROST_PROTECTION_TEMPERATURE, -30),
				(circuit, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.HEAT_CALCULATION_MODE,
				 snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE),
				(circuit, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, request),
				(circuit, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MINIMUM_FLOW_TEMPERATURE, self.MINIMUM_FLOW),
				(circuit, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE, self.MAXIMUM_FLOW),
				(circuit, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.ROOM_SENSOR_INFLUENCE, 0),
			])
		for consumer in [line, *self._circuits(), self._programList['dhw']]:
			for parameter, value in (
				(snc.ConsumerParameterId.PRIORITY, 0),
				(snc.ConsumerParameterId.TEMPERATURE_COMPENSATION, 0),
				(snc.ConsumerParameterId.HEAT_EXTRICATION_ENABLED, 0),
			):
				settings.append((consumer, snc.ProgramType.CONSUMER, parameter, value))
		dhw = self._programList['dhw']
		for parameter, value in (
			(snc.DhwParameterId.WORK_MODE, self.DHW_OFF),
			(snc.DhwParameterId.TEMPERATURE_COMFORT, self.DHW_REQUEST),
			(snc.DhwParameterId.ANTILEGION, 0),
			(snc.DhwParameterId.DHW_RELIEF, 0),
			(snc.DhwParameterId.CIRCULATION_MODE, self.DHW_OFF),
		):
			settings.append((dhw, snc.ProgramType.DHW, parameter, value))
		cascade = self._programList['cascade']
		for parameter, value in (
			(snc.CascadeManagerParameterId.MINIMUM_REQUIRED_TEMPERATURE, 0),
			(snc.CascadeManagerParameterId.MAXIMUM_REQUIRED_TEMPERATURE, self.MAXIMUM_FLOW),
			(snc.CascadeManagerParameterId.TEMPERATURE_OFFSET, 0),
		):
			settings.append((cascade, snc.ProgramType.CASCADE_MANAGER, parameter, value))
		for name in ('boiler_1', 'boiler_2'):
			boiler = self._programList[name]
			settings.append((boiler, snc.ProgramType.TEMPERATURE_GENERATOR,
				snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION, 0))
		return settings

	def _validate_topology(self):
		programs = self._programList
		ids = [program.get_id() for program in programs.values()]
		if len(set(ids)) != len(ids):
			raise RuntimeError('Повторяющиеся ID программ')
		line = programs['heating_line']
		if self.read_parameter(line, snc.ProgramType.PROGRAM, snc.ProgramParameterId.SCHEME) != snc.ProgramScheme['CIRCUIT_HEATING_LINE']:
			raise RuntimeError('Для теплотрассы не выбрана схема «Теплотрасса»')
		for consumer, source in [
			(line, programs['cascade']),
			*((consumer, line) for consumer in [*self._circuits(), programs['dhw']]),
		]:
			if self.read_parameter(consumer, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID) != source.get_id():
				raise RuntimeError('Неверный источник тепла в цепочке потребитель → теплотрасса → каскад')
		for index, name in enumerate(('boiler_1', 'boiler_2')):
			if self.read_parameter(programs['cascade'], snc.ProgramType.CASCADE_MANAGER,
				snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID, index) != programs[name].get_id():
				raise RuntimeError('К каскаду должны быть подключены оба котла')
		for circuit in [line, *self._circuits()]:
			if not circuit.get_output_channel('pump').is_mapped():
				raise RuntimeError('Не назначен насос отопительного контура')
			if any(circuit.get_input_channel(name).is_mapped() for name in ('thermostat', 'outsideRequest', 'pumpControl')):
				raise RuntimeError('Посторонние входы могут влиять на насос контура')

	def _demand(self, program):
		return self.read_parameter(program, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.REQUIRED_TEMPERATURE)

	def _run_test(self, sequence):
		self._status = 'FAIL'
		try:
			self._validate_topology()
			sensors = [program.get_input_channel('temperature') for program in [
				self._programList['heating_line'], *self._circuits(),
				self._programList['dhw'], self._programList['cascade'],
			]]
			outdoor = self._programList['outdoor'].get_input_channel('outdoorTemperature')
			with self.test_configuration(self._settings(), [*sensors, outdoor]):
				for sensor in sensors:
					self.set_sensor_value(sensor, self.SENSOR_TEMPERATURE)
				self.set_sensor_value(outdoor, self.OUTDOOR_TEMPERATURE)
				sequence()
				self._status = 'OK'
		except RuntimeError as error:
			self._status = 'FAIL'
			print_error(str(error))
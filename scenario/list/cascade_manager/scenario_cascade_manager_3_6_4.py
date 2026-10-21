from consoleLog import print_error, print_log
from scenario.base.cascade_manager import CascadeManagerScenario
import smartnet.constants as snc


class Scenario(CascadeManagerScenario):
	REQUEST_CASES = ((40, 50), (60, 50), (40, 50))
	TEST_SENSOR_TEMPERATURE = 30
	MINIMUM_FLOW_TEMPERATURE = 5
	MAXIMUM_TEST_TEMPERATURE = 90

	def get_scenario_title(self):
		return 'Cascade manager: required temperature follows the highest consumer request'

	def get_scenario_description(self):
		return (
			'Требуемая температура каскада равна максимальному запросу потребителей: '
			'выбор максимума, смена лидера и снижение запроса'
		)

	def get_checklist_id(self):
		return '3.6.4'

	def get_required_programs(self):
		return {
			'heating_circuit_1': snc.ProgramType.HEATING_CIRCUIT,
			'heating_circuit_2': snc.ProgramType.HEATING_CIRCUIT,
			'cascade': snc.ProgramType.CASCADE_MANAGER,
			'boiler_1': snc.ProgramType.BOILER,
			'boiler_2': snc.ProgramType.BOILER,
		}

	def get_default_preset(self):
		return 'cascade_manager_3_6_4'

	def requests_match(self, circuits, requests):
		for circuit, expected in zip(circuits, requests):
			actual = self.read_parameter(
				circuit, snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
			)
			if abs(actual - expected) > self.TEMPERATURE_TOLERANCE:
				return False
		return True

	def run(self):
		self._status = 'FAIL'
		cascade = self._programList['cascade']
		circuits = [self._programList[f'heating_circuit_{index}'] for index in (1, 2)]
		parameter_type = snc.ProgramType.CASCADE_MANAGER
		parameter_id = snc.CascadeManagerParameterId
		settings = [
			(cascade, parameter_type, parameter_id.MINIMUM_REQUIRED_TEMPERATURE, 0),
			(cascade, parameter_type, parameter_id.MAXIMUM_REQUIRED_TEMPERATURE, self.MAXIMUM_TEST_TEMPERATURE),
		]
		for circuit, request in zip(circuits, self.REQUEST_CASES[0]):
			settings.extend([
				(circuit, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE, self.MAXIMUM_TEST_TEMPERATURE),
				(circuit, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MINIMUM_FLOW_TEMPERATURE, self.MINIMUM_FLOW_TEMPERATURE),
				(circuit, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.HEAT_CALCULATION_MODE, snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE),
				(circuit, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, request),
				(circuit, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.TEMPERATURE_COMPENSATION, 0),
			])
		sensors = [cascade.get_input_channel('temperature')]
		sensors.extend(circuit.get_input_channel('temperature') for circuit in circuits)
		try:
			with self.test_configuration(settings, sensors):
				for sensor in sensors:
					self.set_sensor_value(sensor, self.TEST_SENSOR_TEMPERATURE)
				for requests in self.REQUEST_CASES:
					expected = max(requests)
					print_log(f'Запросы контуров {requests} °C, ожидаемая температура каскада {expected} °C')
					for circuit, request in zip(circuits, requests):
						self.write_parameter(
							circuit, snc.ProgramType.CIRCUIT,
							snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, request,
						)
					self.require_stable(
						lambda: (
							self.requests_match(circuits, requests)
							and self.required_temperature_is(expected)
						),
						f'Не подтверждён максимум запросов {requests}: '
						f'ожидалась температура каскада {expected} °C',
					)
				self._status = 'OK'
		except RuntimeError as exc:
			print_error(str(exc))
			self._status = 'FAIL'
		if self._status == 'OK':
			print_log('Выбор максимального запроса потребителей каскада проверен')
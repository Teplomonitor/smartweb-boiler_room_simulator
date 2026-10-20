from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
import smartnet.remoteControl as sr


class Scenario(Parent):
	REQUIRED_TEMPERATURE_TIMEOUT = 90
	TEMPERATURE_TOLERANCE = 0.2
	TEST_MINIMUM_FLOW_TEMPERATURE = 5
	TEST_MAXIMUM_FLOW_TEMPERATURE = 110
	TEST_MINIMUM_TEMPERATURE_RESTRICTION = 1
	TEST_NEGATIVE_SHIFT = -10
	TEST_POSITIVE_SHIFT = 5

	CIRCUIT_PARAMETERS = (
		snc.CircuitParameterId.HEAT_CALCULATION_MODE,
		snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE,
		snc.CircuitParameterId.MINIMUM_FLOW_TEMPERATURE,
		snc.CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE,
	)

	def get_scenario_title(self):
		return 'Boiler: required temperature follows the highest consumer request'

	def get_scenario_description(self):
		return (
			'Требуемая температура котла равна максимальному запросу контуров '
			'с учётом температурного сдвига и ограничений котла по минимуму и максимуму'
		)

	def get_checklist_id(self):
		return '3.5.4'

	def get_required_programs(self):
		return {
			'heating_circuit_1': snc.ProgramType.HEATING_CIRCUIT,
			'heating_circuit_2': snc.ProgramType.HEATING_CIRCUIT,
			'heating_circuit_3': snc.ProgramType.HEATING_CIRCUIT,
			'heating_circuit_4': snc.ProgramType.HEATING_CIRCUIT,
			'boiler': snc.ProgramType.BOILER,
		}

	def get_default_preset(self):
		return 'boiler_3_5_4'

	def force_preset_load(self):
		return True

	def _read_parameter(self, program_type, parameter_id, program_id):
		parameter = sr.RemoteControlParameter(
			programType=program_type,
			parameterId=parameter_id,
			programId=program_id,
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def _write_parameter(self, program_type, parameter_id, program_id, value):
		parameter = sr.RemoteControlParameter(
			programType=program_type,
			parameterId=parameter_id,
			parameterValue=value,
			programId=program_id,
		)
		return parameter.write()

	def _set_circuit_request(self, circuit, flow_temperature, compensation):
		program_id = circuit.get_id()
		return all((
			self._write_parameter(
				snc.ProgramType.CIRCUIT,
				snc.CircuitParameterId.HEAT_CALCULATION_MODE,
				program_id,
				snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
			),
			self._write_parameter(
				snc.ProgramType.CIRCUIT,
				snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE,
				program_id,
				flow_temperature,
			),
			self._write_parameter(
				snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.TEMPERATURE_COMPENSATION,
				program_id,
				compensation,
			),
		))

	def _requests_match(self, circuits, expected_requests):
		for circuit, expected in zip(circuits, expected_requests):
			flow_temperature = self._read_parameter(
				snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
				circuit.get_id(),
			)
			compensation = self._read_parameter(
				snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.TEMPERATURE_COMPENSATION,
				circuit.get_id(),
			)
			if (
				flow_temperature is None
				or compensation is None
				or abs(flow_temperature + compensation - expected) > self.TEMPERATURE_TOLERANCE
			):
				return False
		return True

	def _boiler_required_temperature_is(self, expected):
		actual = self._read_parameter(
			snc.ProgramType.TEMPERATURE_SOURCE,
			snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE,
			self._boiler.get_id(),
		)
		return actual is not None and abs(actual - expected) <= self.TEMPERATURE_TOLERANCE

	def _check_requests(self, circuits, expected_requests, minimum, maximum, description):
		if not self.wait_event(
			lambda: self._requests_match(circuits, expected_requests),
			self.REQUIRED_TEMPERATURE_TIMEOUT,
		):
			print_error(f'Не удалось получить ожидаемые запросы контуров: {description}')
			return False

		expected_boiler_temperature = max(minimum, min(maximum, max(expected_requests)))
		print_log(
			f'{description}: запросы контуров {expected_requests}, '
			f'ожидаемая уставка котла {expected_boiler_temperature:.1f} °C'
		)
		if not self.wait_event(
			lambda: self._boiler_required_temperature_is(expected_boiler_temperature),
			self.REQUIRED_TEMPERATURE_TIMEOUT,
		):
			actual = self._read_parameter(
				snc.ProgramType.TEMPERATURE_SOURCE,
				snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE,
				self._boiler.get_id(),
			)
			print_error(
				f'Неверная требуемая температура котла ({description}): '
				f'ожидалось {expected_boiler_temperature:.1f} °C, получено {actual}'
			)
			return False
		return True

	def run(self):
		self._boiler = self._programList['boiler']
		circuits = [
			self._programList[f'heating_circuit_{index}']
			for index in range(1, 5)
		]
		minimum_temperature = self._boiler.get_minimum_temperature()
		maximum_temperature = self._boiler.get_maximum_temperature()
		initial_minimum_restriction = self._boiler.get_minimum_temperature_restriction()

		if (
			minimum_temperature is None
			or maximum_temperature is None
			or initial_minimum_restriction is None
			or minimum_temperature >= maximum_temperature
		):
			print_error('Не удалось прочитать корректные границы температуры котла')
			self._status = 'FAIL'
			return

		initial_parameters = []
		for circuit in circuits:
			for parameter_id in self.CIRCUIT_PARAMETERS:
				parameter_value = self._read_parameter(
					snc.ProgramType.CIRCUIT,
					parameter_id,
					circuit.get_id(),
				)
				if parameter_value is None:
					print_error(f'Не удалось прочитать параметры контура {circuit.get_title()}')
					self._status = 'FAIL'
					return
				initial_parameters.append((snc.ProgramType.CIRCUIT, parameter_id, circuit.get_id(), parameter_value))

			compensation = self._read_parameter(
				snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.TEMPERATURE_COMPENSATION,
				circuit.get_id(),
			)
			if compensation is None:
				print_error(f'Не удалось прочитать температурный сдвиг контура {circuit.get_title()}')
				self._status = 'FAIL'
				return
			initial_parameters.append((
				snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.TEMPERATURE_COMPENSATION,
				circuit.get_id(),
				compensation,
			))

		initial_parameters.append((
			snc.ProgramType.TEMPERATURE_GENERATOR,
			snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
			self._boiler.get_id(),
			initial_minimum_restriction,
		))

		try:
			print_log('Временно включаем ограничение минимальной температуры котла')
			if not self._write_parameter(
				snc.ProgramType.TEMPERATURE_GENERATOR,
				snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
				self._boiler.get_id(),
				self.TEST_MINIMUM_TEMPERATURE_RESTRICTION,
			):
				print_error('Не удалось включить ограничение минимальной температуры котла')
				self._status = 'FAIL'
				return

			for circuit in circuits:
				program_id = circuit.get_id()
				if not self._write_parameter(
					snc.ProgramType.CIRCUIT,
					snc.CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE,
					program_id,
					self.TEST_MAXIMUM_FLOW_TEMPERATURE,
				) or not self._write_parameter(
					snc.ProgramType.CIRCUIT,
					snc.CircuitParameterId.MINIMUM_FLOW_TEMPERATURE,
					program_id,
					self.TEST_MINIMUM_FLOW_TEMPERATURE,
				):
					print_error(f'Не удалось подготовить температурный диапазон контура {circuit.get_title()}')
					self._status = 'FAIL'
					return

			print_log('Проверяем ограничение снизу: оба запроса ниже минимума котла')
			if not all(
				self._set_circuit_request(circuit, self.TEST_MINIMUM_FLOW_TEMPERATURE, self.TEST_NEGATIVE_SHIFT)
				for circuit in circuits
			):
				print_error('Не удалось задать низкие запросы контуров')
				self._status = 'FAIL'
				return
			minimum_request = self.TEST_MINIMUM_FLOW_TEMPERATURE + self.TEST_NEGATIVE_SHIFT
			if not self._check_requests(
				circuits,
				[minimum_request, minimum_request],
				minimum_temperature,
				maximum_temperature,
				'ограничение минимальной температуры',
			):
				self._status = 'FAIL'
				return

			request_span = maximum_temperature - minimum_temperature
			request_levels = [
				round(minimum_temperature + request_span * fraction, 1)
				for fraction in (0.2, 0.4, 0.6, 0.8)
			]
			if min(
				request_levels[index + 1] - request_levels[index]
				for index in range(len(request_levels) - 1)
			) <= 2 * self.TEMPERATURE_TOLERANCE:
				print_error('Диапазон температуры котла слишком узкий для сравнения запросов контуров')
				self._status = 'FAIL'
				return
			compensation = self.TEST_POSITIVE_SHIFT
			print_log('Проверяем выбор максимального запроса при смене лидирующего контура')
			for winner_index in range(len(circuits)):
				expected_requests = [
					request_levels[(index - winner_index - 1) % len(request_levels)]
					for index in range(len(circuits))
				]
				for circuit, expected_request in zip(circuits, expected_requests):
					if not self._set_circuit_request(
						circuit,
						expected_request - compensation,
						compensation,
					):
						print_error(f'Не удалось задать запросы для проверки контура {winner_index + 1}')
						self._status = 'FAIL'
						return
				if not self._check_requests(
					circuits,
					expected_requests,
					minimum_temperature,
					maximum_temperature,
					f'контур {winner_index + 1} имеет максимальный запрос',
				):
					self._status = 'FAIL'
					return

			print_log('Проверяем ограничение сверху: запрос контура выше максимума котла с учётом сдвига')
			maximum_request = self.TEST_MAXIMUM_FLOW_TEMPERATURE + compensation
			maximum_test_requests = [maximum_request] + [
				round(minimum_temperature + request_span * fraction, 1)
				for fraction in (0.2, 0.4, 0.6)
			]
			for circuit, expected_request in zip(circuits, maximum_test_requests):
				if not self._set_circuit_request(
					circuit,
					expected_request - compensation,
					compensation,
				):
					print_error('Не удалось задать запрос выше максимума котла')
					self._status = 'FAIL'
					return
			if not self._check_requests(
				circuits,
				maximum_test_requests,
				minimum_temperature,
				maximum_temperature,
				'ограничение максимальной температуры',
			):
				self._status = 'FAIL'
				return

			print_log('Проверка требуемой температуры котла прошла успешно')
			self._status = 'OK'
		finally:
			restore_failed = False
			for program_type, parameter_id, program_id, value in reversed(initial_parameters):
				if not self._write_parameter(program_type, parameter_id, program_id, value):
					print_error(
						f'Не удалось восстановить параметр {program_type}.{parameter_id} '
						f'программы {program_id}'
					)
					restore_failed = True
			if restore_failed:
				self._status = 'FAIL'

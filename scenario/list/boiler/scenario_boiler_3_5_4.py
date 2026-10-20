from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
import smartnet.remoteControl as sr


class Scenario(Parent):
	REQUIRED_TEMPERATURE_TIMEOUT = 90
	REQUIRED_TEMPERATURE_HOLD_DURATION = 5
	TEMPERATURE_TOLERANCE = 0.2
	BOUNDARY_OFFSET = 2
	TEST_MINIMUM_FLOW_TEMPERATURE = 5
	TEST_MINIMUM_CONSTANT_FLOW_TEMPERATURE = 10
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
		if not circuits or len(circuits) != len(expected_requests):
			return False
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
		if not circuits or len(circuits) != len(expected_requests):
			print_error(f'Неверное количество ожидаемых запросов: {description}')
			return False
		if not self.wait_event(
			lambda: self._requests_match(circuits, expected_requests),
			self.REQUIRED_TEMPERATURE_TIMEOUT,
		):
			print_error(f'Не удалось получить ожидаемые запросы контуров: {description}')
			self._log_requests(circuits, expected_requests)
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
			self._log_requests(circuits, expected_requests)
			return False
		if not self.wait_state_permanence(
			lambda: (
				self._requests_match(circuits, expected_requests)
				and self._boiler_required_temperature_is(expected_boiler_temperature)
			),
			self.REQUIRED_TEMPERATURE_HOLD_DURATION,
		):
			print_error(f'Запросы или уставка котла не удерживаются: {description}')
			self._log_requests(circuits, expected_requests)
			return False
		return True

	def _log_requests(self, circuits, expected_requests):
		for circuit, expected in zip(circuits, expected_requests):
			flow = self._read_parameter(
				snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
				circuit.get_id(),
			)
			shift = self._read_parameter(
				snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.TEMPERATURE_COMPENSATION,
				circuit.get_id(),
			)
			print_error(
				f'Контур {circuit.get_id()}: температура {flow}, '
				f'сдвиг {shift}, ожидаемый запрос {expected}'
			)
		actual = self._read_parameter(
			snc.ProgramType.TEMPERATURE_SOURCE,
			snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE,
			self._boiler.get_id(),
		)
		print_error(f'Требуемая температура котла: {actual}')

	def _build_test_cases(self, minimum, maximum):
		# Keep mixed-shift cases inside both the boiler and circuit ranges.
		lower = max(minimum, self.TEST_MINIMUM_CONSTANT_FLOW_TEMPERATURE + self.TEST_POSITIVE_SHIFT)
		upper = min(maximum, self.TEST_MAXIMUM_FLOW_TEMPERATURE + self.TEST_NEGATIVE_SHIFT)
		span = upper - lower
		if span * 0.05 <= 2 * self.TEMPERATURE_TOLERANCE:
			raise ValueError('Диапазон температуры слишком узкий для различения запросов')

		def level(fraction):
			return round(lower + span * fraction, 1)

		cases = []
		def add_case(description, requests, shifts=None):
			cases.append((description, requests, [0] * 4 if shifts is None else shifts))

		low_request = self.TEST_MINIMUM_CONSTANT_FLOW_TEMPERATURE + self.TEST_NEGATIVE_SHIFT
		if low_request >= minimum:
			raise ValueError('Низкий тестовый запрос не ниже минимума котла')
		add_case('все запросы ниже минимума', [low_request] * 4, [self.TEST_NEGATIVE_SHIFT] * 4)

		for winner, fraction in enumerate((0.8, 0.5, 0.9, 0.65)):
			requests = [level(value) for value in (0.1, 0.2, 0.3, 0.1)]
			requests[winner] = level(fraction)
			add_case(f'контур {winner + 1} лидирует, максимум меняется', requests, [self.TEST_POSITIVE_SHIFT] * 4)

		add_case(
			'сдвиги меняют лидера относительно исходных температур',
			[level(value) for value in (0.4, 0.45, 0.1, 0.2)],
			[self.TEST_NEGATIVE_SHIFT, self.TEST_POSITIVE_SHIFT, 0, 0],
		)
		for description, fractions in (
			('два равных максимума', (0.7, 0.7, 0.4, 0.1)),
			('первый лидер снижает запрос, второй удерживает максимум', (0.2, 0.7, 0.4, 0.1)),
			('второй лидер снижает запрос, максимум падает', (0.2, 0.3, 0.4, 0.1)),
			('новый лидер после равенства', (0.2, 0.3, 0.4, 0.8)),
		):
			add_case(description, [level(value) for value in fractions])

		# Equal requests isolate clamping from selection of the winning circuit.
		for description, request in (
			('ниже минимума', minimum - self.BOUNDARY_OFFSET),
			('ровно минимум', minimum),
			('выход из нижнего ограничения', minimum + self.BOUNDARY_OFFSET),
			('выше максимума', maximum + self.BOUNDARY_OFFSET),
			('ровно максимум', maximum),
			('выход из верхнего ограничения', maximum - self.BOUNDARY_OFFSET),
		):
			shift = self.TEST_NEGATIVE_SHIFT if request < self.TEST_MINIMUM_CONSTANT_FLOW_TEMPERATURE else 0
			add_case(description, [request] * 4, [shift] * 4)

		extreme = self.TEST_MAXIMUM_FLOW_TEMPERATURE + self.TEST_POSITIVE_SHIFT
		if extreme <= maximum:
			raise ValueError('Экстремальный запрос не превышает максимум котла')
		add_case('защита от экстремального запроса', [extreme] * 4, [self.TEST_POSITIVE_SHIFT] * 4)
		add_case('возврат после экстремального запроса', [level(0.4)] * 4)

		for description, requests, shifts in cases:
			for request, shift in zip(requests, shifts):
				if not self.TEST_MINIMUM_CONSTANT_FLOW_TEMPERATURE <= request - shift <= self.TEST_MAXIMUM_FLOW_TEMPERATURE:
					raise ValueError(f'Уставка контура вне тестового диапазона: {description}')
		return cases

	def run(self):
		self._status = 'FAIL'
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

		try:
			test_cases = self._build_test_cases(minimum_temperature, maximum_temperature)
		except ValueError as error:
			print_error(str(error))
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

			for description, expected_requests, shifts in test_cases:
				print_log(description)
				for circuit, expected_request, shift in zip(circuits, expected_requests, shifts):
					if not self._set_circuit_request(
						circuit,
						expected_request - shift,
						shift,
					):
						print_error(f'Не удалось задать запрос контура {circuit.get_id()}: {description}')
						self._status = 'FAIL'
						return
				if not self._check_requests(
					circuits,
					expected_requests,
					minimum_temperature,
					maximum_temperature,
					description,
				):
					self._status = 'FAIL'
					return

			self._status = 'OK'
		finally:
			restore_failed = False
			for program_type, parameter_id, program_id, value in reversed(initial_parameters):
				try:
					restored = self._write_parameter(program_type, parameter_id, program_id, value)
				except Exception as error:
					print_error(f'Ошибка восстановления параметра: {error}')
					restored = False
				if not restored:
					print_error(
						f'Не удалось восстановить параметр {program_type}.{parameter_id} '
						f'программы {program_id}'
					)
					restore_failed = True
			if restore_failed:
				self._status = 'FAIL'
		if self._status == 'OK':
			print_log('Проверка требуемой температуры котла и восстановление параметров прошли успешно')

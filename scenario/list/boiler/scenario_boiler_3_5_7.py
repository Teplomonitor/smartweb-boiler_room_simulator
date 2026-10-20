import math

from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
import smartnet.remoteControl as sr


class Scenario(Parent):
	TEST_SETPOINTS = (45, 60, 45)
	REQUEST_TIMEOUT = 90
	SETTLING_TIMEOUT = 15 * 60
	CONTROL_DURATION = 2 * 60
	CONTROL_TIMEOUT = 15 * 60
	LARGE_ERROR_TIMEOUT = 2 * 60
	AVERAGE_ERROR_LIMIT = 3
	LARGE_ERROR_LIMIT = 5
	REQUEST_TOLERANCE = 0.2
	MINIMUM_POWER_CHANGE = 5
	CIRCUIT_SETTINGS = (
		('heatCalculationMode', snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE),
		('temperatureCompensation', 0),
		('requiredConstantFlowTemperature', TEST_SETPOINTS[0]),
	)

	def get_scenario_title(self):
		return 'Boiler: analog power maintains the required temperature'

	def get_scenario_description(self):
		return (
			'Котёл управляет аналоговым выходом мощности по текущей и требуемой '
			'температурам и поддерживает температуру при повышении и снижении '
			'запроса единственного отопительного контура. Датчики работают автоматически.'
		)

	def get_checklist_id(self):
		return '3.5.7'

	def get_required_programs(self):
		return {
			'heating_circuit': snc.ProgramType.HEATING_CIRCUIT,
			'boiler': snc.ProgramType.BOILER,
		}

	def get_default_preset(self):
		return 'boiler_3_5_7'

	def force_preset_load(self):
		return True

	def _write_circuit_parameter(self, circuit, name, value):
		# Program.write_parameter_value() returns the value, not write status.
		# In particular, a successfully written zero is not a failure.
		parameter = sr.RemoteControlParameter(
			parameterCode=circuit.get_parameter_code(name),
			programId=circuit.get_id(),
			parameterValue=value,
		)
		return parameter.write()

	def _read_required_temperature(self):
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.TEMPERATURE_SOURCE,
			parameterId=snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE,
			programId=self._boiler.get_id(),
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def _request_matches(self):
		actual = self._read_required_temperature()
		return (
			actual is not None and math.isfinite(actual)
			and abs(actual - self._expected_temperature) <= self.REQUEST_TOLERANCE
		)

	def _checked_required_temperature(self):
		actual = self._read_required_temperature()
		if (
			actual is None or not math.isfinite(actual)
			or abs(actual - self._expected_temperature) > self.REQUEST_TOLERANCE
		):
			raise ValueError(f'Потеряна ожидаемая уставка котла: {actual}')
		return actual

	def _sample_temperature(self):
		actual = self._boiler.get_temperature()
		power = self._boiler.get_power_output_percent()
		if actual is None or not math.isfinite(actual):
			raise ValueError('Нет корректной температуры котла')
		if power is None or not math.isfinite(power) or not 0 <= power <= 100:
			raise ValueError('Нет корректного значения аналоговой мощности котла')
		self._minimum_power = min(self._minimum_power, power)
		self._maximum_power = max(self._maximum_power, power)
		self._modulation_seen |= 0 < power < 100
		return actual

	def _temperature_reached(self):
		actual = self._sample_temperature()
		return self._request_matches() and abs(actual - self._expected_temperature) < self.AVERAGE_ERROR_LIMIT

	def _log_diagnostics(self):
		print_error(
			f'Котёл: температура {self._boiler.get_temperature()}, '
			f'ожидаемая уставка {self._expected_temperature}, '
			f'мощность {self._boiler.get_power_output_percent()} %, '
			f'наблюдавшийся диапазон мощности {self._minimum_power:.1f}..{self._maximum_power:.1f} %'
		)
		print_error(
			'Если при 100 % мощности котёл остаётся холоднее уставки, '
			'проверьте мощность котла и тепловую нагрузку в симуляторе.'
		)

	def run(self):
		self._status = 'FAIL'
		self._boiler = self._programList['boiler']
		circuit = self._programList['heating_circuit']
		self._minimum_power = 100
		self._maximum_power = 0
		self._modulation_seen = False
		self._expected_temperature = self.TEST_SETPOINTS[0]

		for sensor in (
			self._boiler.get_input_channel('temperature'),
			circuit.get_input_channel('temperature'),
		):
			if not sensor.is_mapped() or sensor.isManual():
				print_error('Для теста необходимы подключённые автоматические датчики температуры')
				return
		if (
			not self._boiler.get_power_output().is_mapped()
			or self._boiler.get_stage_1().is_mapped()
			or self._boiler.get_output_channel('burner2').is_mapped()
		):
			print_error('Для теста нужна единственная аналоговая ступень котла')
			return

		initial_parameters = []
		for name, _ in self.CIRCUIT_SETTINGS:
			value = circuit.read_parameter_value(name)
			if value is None:
				print_error(f'Не удалось прочитать параметр контура {name}')
				return
			initial_parameters.append((name, value))

		try:
			for name, value in self.CIRCUIT_SETTINGS:
				if not self._write_circuit_parameter(circuit, name, value):
					print_error(f'Не удалось подготовить параметр контура {name}')
					return

			for setpoint in self.TEST_SETPOINTS:
				self._expected_temperature = setpoint
				print_log(f'Запрос потребителя и ожидаемая температура котла: {setpoint} °C')
				if not self._write_circuit_parameter(circuit, 'requiredConstantFlowTemperature', setpoint):
					print_error('Не удалось задать запрос потребителя')
					return
				if not self.wait_event(self._request_matches, self.REQUEST_TIMEOUT):
					print_error('Котёл не получил ожидаемую уставку')
					self._log_diagnostics()
					return
				if not self.wait_event(self._temperature_reached, self.SETTLING_TIMEOUT):
					print_error('Котёл не вышел к требуемой температуре')
					self._log_diagnostics()
					return
				if not self.wait_value_maintaining(
					self._sample_temperature,
					self._checked_required_temperature,
					duration=self.CONTROL_DURATION,
					timeout=self.CONTROL_TIMEOUT,
					dtTimeout=self.LARGE_ERROR_TIMEOUT,
					dtAvrMax=self.AVERAGE_ERROR_LIMIT,
					dtMax=self.LARGE_ERROR_LIMIT,
				):
					self._log_diagnostics()
					return

			if not self._modulation_seen or self._maximum_power - self._minimum_power < self.MINIMUM_POWER_CHANGE:
				print_error('Не обнаружено изменения аналоговой мощности котла')
				self._log_diagnostics()
				return
			self._status = 'OK'
		except ValueError as error:
			print_error(str(error))
		finally:
			for name, value in reversed(initial_parameters):
				try:
					restored = self._write_circuit_parameter(circuit, name, value)
				except Exception as error:
					print_error(f'Ошибка восстановления параметра {name}: {error}')
					restored = False
				if not restored:
					print_error(f'Не удалось восстановить параметр контура {name}')
					self._status = 'FAIL'
		if self._status == 'OK':
			print_log('Котёл поддерживает температуру аналоговой мощностью; параметры восстановлены')
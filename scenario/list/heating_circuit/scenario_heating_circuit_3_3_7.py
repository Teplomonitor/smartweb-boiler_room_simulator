from consoleLog import print_log
from scenario.base.heating_circuit_line import HeatingCircuitLineScenario
import smartnet.constants as snc


class Scenario(HeatingCircuitLineScenario):
	LINE_BASE_SETPOINT = 45
	CIRCUIT_REQUESTS = (35, 40)
	# Explicit reference points: (setpoints, enabled circuits, line request).
	PHASES = (
		((35, 40), (False, False), 45),
		((35, 40), (True, True), 45),
		((45, 40), (True, True), 45),
		((50, 40), (True, False), 50),
		((50, 60), (True, True), 60),
		((55, 40), (True, True), 55),
		((55, 60), (True, True), 60),
		((55, 60), (True, False), 55),
		((55, 60), (False, False), 45),
		((35, 60), (False, True), 60),
		((35, 40), (False, False), 45),
	)

	def get_checklist_id(self):
		return '3.3.7'

	def get_default_preset(self):
		return 'heating_circuit_3_3_6'

	def get_scenario_title(self):
		return 'Heating circuit: heating line temperature includes downstream requests'

	def get_scenario_description(self):
		return (
			'В режиме теплотрассы требуемая температура также учитывает запрашиваемую '
			'другими контурами температуру: выбирается максимум собственной уставки '
			'45 °C и запросов двух контуров. Проверяются запросы ниже, равные и выше '
			'уставки, смена максимального запроса, его снижение и снятие, повторное '
			'включение и передача температуры каскаду. ГВС отключено.'
		)

	def _settings(self):
		line = self._programList['heating_line']
		# Keep the own request observable even when every downstream circuit is off.
		return [
			(program, program_type, parameter_id,
			 self.PUMP_ALWAYS_ON if program is line
			 and program_type == snc.ProgramType.HEATING_CIRCUIT
			 and parameter_id == snc.HeatingCircuitParameterId.PUMP_MODE else value)
			for program, program_type, parameter_id, value in super()._settings()
		]

	def _requests_match(self, requests, active):
		return all(
			abs(self._demand(program) - (request if enabled else 0)) <= self.TEMPERATURE_TOLERANCE
			for program, request, enabled in zip(
				[*self._circuits(), self._programList['dhw']], [*requests, 0], [*active, False],
			)
		)

	def _line_matches(self, expected):
		line = self._programList['heating_line']
		return (
			line.get_output_channel('pump').get_value() == self.RELAY_ON
			and abs(self._demand(line) - expected) <= self.TEMPERATURE_TOLERANCE
			and self.required_temperature_is(expected)
		)

	def _check_phase(self, requests, active, expected):
		print_log(f'Уставки контуров: {requests}, включены: {active}; запрос теплотрассы: {expected} °C')
		for circuit, request, enabled in zip(self._circuits(), requests, active):
			self.write_parameter(circuit, snc.ProgramType.CIRCUIT,
				snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, request)
			self.write_parameter(circuit, snc.ProgramType.HEATING_CIRCUIT,
				snc.HeatingCircuitParameterId.PUMP_MODE, self.PUMP_ALWAYS_ON if enabled else self.PUMP_ALWAYS_OFF)
		if not self.wait_event(lambda: self._requests_match(requests, active), self.CONSUMER_TIMEOUT):
			raise RuntimeError(f'Не установились запросы контуров: {requests}, включены: {active}')
		# Observe beyond selector reset and pump overrun to reject stale maxima.
		matches = lambda: self._requests_match(requests, active) and self._line_matches(expected)
		if not self.wait_state_permanence(matches, self.OBSERVATION_DURATION, self.LINE_TIMEOUT):
			raise RuntimeError(f'Теплотрасса или каскад не установили требуемую температуру {expected} °C')

	def _sequence(self):
		for requests, active, expected in self.PHASES:
			self._check_phase(requests, active, expected)

	def run(self):
		self._run_test(self._sequence)
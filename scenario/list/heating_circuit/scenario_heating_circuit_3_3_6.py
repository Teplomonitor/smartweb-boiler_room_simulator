from consoleLog import print_log
from scenario.base.heating_circuit_line import HeatingCircuitLineScenario
import smartnet.constants as snc


class Scenario(HeatingCircuitLineScenario):
	PHASES = (
		(False, False, False),
		(True, False, False),
		(True, True, False),
		(False, True, False),
		(False, False, False),
		(False, False, True),
		(True, True, True),
		(False, False, True),
		(False, False, False),
		(True, False, False),
		(False, False, False),
	)

	def get_checklist_id(self):
		return '3.3.6'

	def get_default_preset(self):
		return 'heating_circuit_3_3_6'

	def get_scenario_title(self):
		return 'Heating circuit: heating line pump follows downstream heat demand'

	def get_scenario_description(self):
		return (
			'Теплотрасса от каскада двух котлов: насос включается по запросам '
			'двух контуров и ГВС, продолжает работать при снятии части запросов, '
			'выключается после последнего запроса и запускается повторно'
		)

	def _requests_match(self, active):
		consumers = [*self._circuits(), self._programList['dhw']]
		requests = [*self.CIRCUIT_REQUESTS, self.DHW_REQUEST]
		return all(
			abs(self._demand(program) - (request if enabled else 0)) <= self.TEMPERATURE_TOLERANCE
			for program, request, enabled in zip(consumers, requests, active)
		)

	def _line_matches(self, active):
		line = self._programList['heating_line']
		expected_pump = self.RELAY_ON if any(active) else self.RELAY_OFF
		if line.get_output_channel('pump').get_value() != expected_pump:
			return False
		expected = max((request for request, enabled in zip(
			[*self.CIRCUIT_REQUESTS, self.DHW_REQUEST], active,
		) if enabled), default=0)
		if abs(self._demand(line) - expected) > self.TEMPERATURE_TOLERANCE:
			return False
		# The cascade must receive the real propagated demand, not just a local
		# pump command. Its own idle temperature policy is outside this test.
		return not any(active) or self.required_temperature_is(expected)

	def _check_phase(self, active):
		print_log(f'Запросы: контур 1={active[0]}, контур 2={active[1]}, ГВС={active[2]}')
		for circuit, enabled in zip(self._circuits(), active[:2]):
			self.write_parameter(circuit, snc.ProgramType.HEATING_CIRCUIT,
				snc.HeatingCircuitParameterId.PUMP_MODE, self.PUMP_ALWAYS_ON if enabled else self.PUMP_ALWAYS_OFF)
		self.write_parameter(self._programList['dhw'], snc.ProgramType.DHW,
			snc.DhwParameterId.WORK_MODE, self.DHW_COMFORT if active[2] else self.DHW_OFF)
		if not self.wait_event(lambda: self._requests_match(active), self.CONSUMER_TIMEOUT):
			raise RuntimeError(f'Потребители не установили/не сняли запросы: {active}')
		matches = lambda: self._requests_match(active) and self._line_matches(active)
		if not self.wait_state_permanence(matches, self.OBSERVATION_DURATION, self.LINE_TIMEOUT):
			raise RuntimeError(f'Насос или запрос теплотрассы не соответствует потребителям: {active}')

	def _sequence(self):
		for active in self.PHASES:
			self._check_phase(active)

	def run(self):
		self._run_test(self._sequence)
from scenario.base.heating_circuit_demand import HeatingCircuitDemandScenario


class Scenario(HeatingCircuitDemandScenario):
	TEST_ROOM = False

	def get_checklist_id(self):
		return '3.3.5.1'

	def get_scenario_title(self):
		return 'Heating circuit: weather curve demand'

	def get_scenario_description(self):
		return (
			'При отключённой комнатной коррекции запрос соответствует погодному графику '
			'с наклоном 0.8: +10, 0, -10 и снова +10 C. '
			'Изменение комнатной температуры не влияет на запрос.'
		)

	def _sequence(self):
		# Reference points from CircuitProgram::computeCurveBySlope, slope=80.
		# No duplicate implementation of controller calculations in scenarios.
		for outdoor, room, expected in (
			(10, 20, 28.6), (0, 18, 36), (-10, 22, 42.3), (10, 20, 28.6),
			(10, 18, 28.6), (10, 22, 28.6),
		):
			self._check_point(outdoor, room, self.ROOM_SETPOINT, expected)

	def run(self):
		self._run_test(self._sequence)
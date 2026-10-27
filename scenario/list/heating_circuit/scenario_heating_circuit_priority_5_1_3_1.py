from scenario.base.heating_circuit_priority import HeatingCircuitPriorityScenario


class Scenario(HeatingCircuitPriorityScenario):
	def get_scenario_title(self):
		return 'Heating circuit priority request - opening dynamics threshold'

	def get_scenario_description(self):
		return ('При недогреве подачи ровно «Динамика откр.» запрос GIVE_WAY отсутствует, '
			'при превышении порога появляется; проверяются два значения параметра')

	def get_checklist_id(self):
		return '5.1.3.1'

	def run(self):
		self._run_priority_test()
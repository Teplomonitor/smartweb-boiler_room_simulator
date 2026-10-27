from scenario.base.dhw_priority import DhwPriorityScenario


class Scenario(DhwPriorityScenario):
	def get_scenario_title(self):
		return 'DHW priority request disabled after prolonged underheating'

	def get_scenario_description(self):
		return 'ГВС снимает запрос приоритета, если источник горячий, но нагрев воды длительно отсутствует'

	def get_checklist_id(self):
		return '5.1.1.3'

	def run(self):
		self._run_priority_test(verify_cold_suppression=True)

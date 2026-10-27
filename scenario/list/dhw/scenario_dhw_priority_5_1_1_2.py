from scenario.base.dhw_priority import DhwPriorityScenario


class Scenario(DhwPriorityScenario):
	def get_scenario_title(self):
		return 'DHW priority request - flow-through scheme'

	def get_scenario_description(self):
		return 'Проточная ГВС отправляет GIVE_WAY, когда требуемая температура выше температуры котла'

	def get_checklist_id(self):
		return '5.1.1.2'

	def get_default_preset(self):
		return 'dhw_priority_flow_through'

	def run(self):
		self._run_priority_test(flow_through=True)

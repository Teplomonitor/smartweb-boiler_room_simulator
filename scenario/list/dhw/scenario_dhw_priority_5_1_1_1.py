from consoleLog import print_error, print_log
from scenario.base.dhw_priority import DhwPriorityScenario


class Scenario(DhwPriorityScenario):
	def get_scenario_title(self):
		return 'DHW priority request - standard scheme'

	def get_scenario_description(self):
		return 'ГВС отправляет GIVE_WAY во время нагрева воды по стандартной схеме'

	def get_checklist_id(self):
		return '5.1.1.1'

	def run(self):
		self._run_priority_test()

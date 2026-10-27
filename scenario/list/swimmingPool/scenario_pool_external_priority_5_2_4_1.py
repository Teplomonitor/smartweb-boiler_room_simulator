from scenario.base.external_priority import ExternalPriorityScenario


class Scenario(ExternalPriorityScenario):
	TARGET = 'pool'
	PRESET = 'swimmingPool'

	def get_scenario_title(self):
		return 'Pool - external priority clears required water temperature'

	def get_scenario_description(self):
		return 'При GIVE_WAY требуемая температура воды равна нулю, после PROCEED восстанавливается'

	def get_checklist_id(self):
		return '5.2.4.1'

	def run(self):
		self._run_external_test('pool')
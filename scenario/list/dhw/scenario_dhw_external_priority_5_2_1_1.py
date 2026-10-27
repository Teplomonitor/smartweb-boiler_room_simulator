from scenario.base.external_priority import ExternalPriorityScenario


class Scenario(ExternalPriorityScenario):
	TARGET = 'dhw'
	PRESET = 'dhw_external_priority'

	def get_scenario_title(self):
		return 'DHW - external priority stops loading pump'

	def get_scenario_description(self):
		return 'Насос загрузки ГВС выключается по GIVE_WAY и снова включается после PROCEED'

	def get_checklist_id(self):
		return '5.2.1.1'

	def run(self):
		self._run_external_test('pump')
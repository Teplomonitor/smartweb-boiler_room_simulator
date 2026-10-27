from scenario.base.external_priority import ExternalPriorityScenario


class Scenario(ExternalPriorityScenario):
	TARGET = 'snow'
	PRESET = 'snowmelter'

	def get_scenario_title(self):
		return 'Snowmelt - external priority stops loading pump'

	def get_scenario_description(self):
		return 'Насос загрузки снеготайки выключается по GIVE_WAY и включается после PROCEED'

	def get_checklist_id(self):
		return '5.2.2.1'

	def run(self):
		self._run_external_test('pump_primary')
from scenario.base.external_priority import ExternalPriorityScenario


class Scenario(ExternalPriorityScenario):
	TARGET = 'snow'
	PRESET = 'snowmelter_relay'
	SNOW_PUMP = 'primaryPump'

	def get_scenario_title(self):
		return 'Snowmelt (relay loading pump) - external priority stops circulation pump'

	def get_scenario_description(self):
		return 'Циркуляционный насос снеготайки выключается по GIVE_WAY и включается после PROCEED'

	def get_checklist_id(self):
		return '5.2.2.5'

	def run(self):
		self._run_external_test('pump')
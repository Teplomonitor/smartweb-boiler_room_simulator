from scenario.base.external_priority import ExternalPriorityScenario


class Scenario(ExternalPriorityScenario):
	ESTIMATED_RUN_SECONDS = 30
	TARGET = 'snow'
	PRESET = 'snowmelter_relay'
	SNOW_PUMP = 'primaryPump'

	def get_scenario_title(self):
		return 'Snowmelt - external priority stops relay loading pump'

	def get_scenario_description(self):
		return 'Релейный насос загрузки снеготайки выключается по GIVE_WAY и включается после PROCEED'

	def get_checklist_id(self):
		return '5.2.2.4'

	def run(self):
		self._run_external_test('pump_primary')
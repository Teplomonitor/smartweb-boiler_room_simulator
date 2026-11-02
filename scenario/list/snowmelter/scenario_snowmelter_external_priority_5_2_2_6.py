from scenario.base.external_priority import ExternalPriorityScenario


class Scenario(ExternalPriorityScenario):
	ESTIMATED_RUN_SECONDS = 40
	TARGET = 'snow'
	PRESET = 'snowmelter_relay'
	SNOW_PUMP = 'primaryPump'

	def get_scenario_title(self):
		return 'Snowmelt (relay loading pump) - frost protection and heat dump override priority'

	def get_scenario_description(self):
		return ('При замерзании теплообменника или сбросе тепла релейный насос загрузки работает '
			'вопреки внешнему GIVE_WAY; циркуляционный насос при замерзании не проверяется')

	def get_checklist_id(self):
		return '5.2.2.6'

	def run(self):
		self._run_external_test('exception')
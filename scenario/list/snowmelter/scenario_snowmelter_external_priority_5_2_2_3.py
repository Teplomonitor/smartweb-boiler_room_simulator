from scenario.base.external_priority import ExternalPriorityScenario


class Scenario(ExternalPriorityScenario):
	TARGET = 'snow'
	PRESET = 'snowmelter'

	def get_scenario_title(self):
		return 'Snowmelt - frost protection and heat dump override priority'

	def get_scenario_description(self):
		return ('При замерзании теплообменника или сбросе тепла насос загрузки работает '
			'вопреки внешнему GIVE_WAY; циркуляционный насос при замерзании не проверяется')

	def get_checklist_id(self):
		return '5.2.2.3'

	def run(self):
		self._run_external_test('exception')
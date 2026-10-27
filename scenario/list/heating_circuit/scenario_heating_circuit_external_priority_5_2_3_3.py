from scenario.base.external_priority import ExternalPriorityScenario


class Scenario(ExternalPriorityScenario):
	TARGET = 'mixed'
	PRESET = 'heating_circuit_external_priority'

	def get_scenario_title(self):
		return 'Heating circuit - frost protection and heat dump override priority'

	def get_scenario_description(self):
		return 'Контур сохраняет работу насоса при замерзании или сбросе тепла вопреки GIVE_WAY'

	def get_checklist_id(self):
		return '5.2.3.3'

	def run(self):
		self._run_external_test('exception')
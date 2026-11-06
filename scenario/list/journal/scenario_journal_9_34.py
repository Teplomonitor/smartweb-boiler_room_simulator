from scenario.base.journal_boiler_faults import JournalBoilerFaultScenario


class Scenario(JournalBoilerFaultScenario):
	LOW_POWER = False
	ESTIMATED_RUN_SECONDS = 3300

	def get_scenario_title(self):
		return 'Journal: low boiler temperature'

	def get_scenario_description(self):
		return ('При работающей первой ступени температура котла 20 °C удерживается ниже '
			'порога разогрева 30 °C в течение 50 минут. Проверяется новая запись '
			'«Низкая температура котла», её важность и номер программы. '
			'Обратка 5 °C исключает аварию низкой мощности; таймер прошивки не ускоряется.')

	def get_checklist_id(self):
		return '9.34'

	def run(self):
		self.run_fault_test()
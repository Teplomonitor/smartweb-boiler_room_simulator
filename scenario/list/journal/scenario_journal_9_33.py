from scenario.base.journal_boiler_faults import JournalBoilerFaultScenario


class Scenario(JournalBoilerFaultScenario):
	ESTIMATED_RUN_SECONDS = 3300

	def get_scenario_title(self):
		return 'Journal: low boiler power'

	def get_scenario_description(self):
		return ('При работающей первой ступени подача 40 °C ниже обратки 40 °C + гистерезис 5 °C '
			'и запроса 70 °C − гистерезис. Через 50 минут проверяется новая запись '
			'«Низкая мощность котла», её важность и номер программы. '
			'Подача выше порога разогрева 30 °C; таймер прошивки не ускоряется.')

	def get_checklist_id(self):
		return '9.33'

	def run(self):
		self.run_fault_test()
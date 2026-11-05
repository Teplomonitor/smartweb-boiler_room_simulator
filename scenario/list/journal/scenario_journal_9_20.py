from scenario.base.journal_overheat import JournalOverheatScenario


class Scenario(JournalOverheatScenario):
	ESTIMATED_RUN_SECONDS = 250

	def get_scenario_title(self):
		return 'Journal: heating circuit overheating'

	def get_scenario_description(self):
		return ('При работающем насосе температура контура выше максимально допустимой на 6 °C '
			'в течение 2 минут: новая запись «температура выше максимально допустимой» '
			'с важностью «Авария» и номером программы; преждевременная запись недопустима.')

	def get_checklist_id(self):
		return '9.20'

	def run(self):
		self.run_overheat_test()
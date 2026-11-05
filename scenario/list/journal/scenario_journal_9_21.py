from scenario.base.journal_overheat import JournalOverheatScenario


class Scenario(JournalOverheatScenario):
	TARGET = 'boiler'
	OVERHEAT_DELAY = 5 * 60
	ESTIMATED_RUN_SECONDS = 430

	def get_scenario_title(self):
		return 'Journal: boiler overheating'

	def get_scenario_description(self):
		return ('Температура котла выше BOILER_COOLING_TEMPERATURE на 5 °C в течение 5 минут: '
			'новая запись «температура выше максимально допустимой» с важностью «Авария» '
			'и номером программы; преждевременная запись недопустима.')

	def get_checklist_id(self):
		return '9.21'

	def run(self):
		self.run_overheat_test()
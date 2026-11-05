from scenario.base.journal_temperature import JournalTemperatureScenario


class Scenario(JournalTemperatureScenario):
	ESTIMATED_RUN_SECONDS = 3900

	def get_scenario_title(self):
		return 'Journal: consumer underheating and recovery'

	def get_scenario_description(self):
		return ('9.16: небольшой недогрев контура 30 минут и ГВС 60 минут; '
			'9.17: после нормализации обеих температур появляются уведомления восстановления. '
			'Один прогон, отдельный результат каждого пункта.')

	def get_checklist_id(self):
		return '9.16, 9.17'

	def get_default_preset(self):
		return 'journal_underheating'

	def run(self):
		self.run_temperature_test()
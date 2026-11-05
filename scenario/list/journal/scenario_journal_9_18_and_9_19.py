from scenario.base.journal_temperature import JournalTemperatureScenario


class Scenario(JournalTemperatureScenario):
	SEVERE = True
	ESTIMATED_RUN_SECONDS = 4000

	def get_scenario_title(self):
		return 'Journal: very low temperature and cascade recovery'

	def get_scenario_description(self):
		return ('9.18: сильный недогрев контура и комнаты 30 минут, котла и каскада 60 минут; '
			'9.19: каскад не сообщает восстановление между минимумом и уставкой, '
			'а сообщает после достижения уставки в течение 30 секунд. Отдельные результаты пунктов.')

	def get_checklist_id(self):
		return '9.18, 9.19'

	def get_default_preset(self):
		return 'journal_low_temperature'

	def run(self):
		self.run_temperature_test()
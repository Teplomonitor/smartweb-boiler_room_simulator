from scenario.base.journal_overheat import JournalOverheatScenario


class Scenario(JournalOverheatScenario):
	TARGET = 'boiler'
	OVERHEAT_DELAY = 5 * 60
	CHECK_RECOVERY = True
	RECOVERY_TEMPERATURE_MARGIN = 1
	SOURCE_TEMPERATURE = (JournalOverheatScenario.BOILER_COOLING_TEMPERATURE
		- JournalOverheatScenario.BOILER_RECOVERY_HYSTERESIS - RECOVERY_TEMPERATURE_MARGIN)
	ESTIMATED_RUN_SECONDS = 550

	def get_scenario_title(self):
		return 'Journal: boiler overheating and recovery'

	def get_scenario_description(self):
		return ('9.21: температура котла выше BOILER_COOLING_TEMPERATURE на 5 °C в течение 5 минут: '
			'новая запись перегрева с важностью «Авария» и номером программы. '
			'9.22: на границе BOILER_COOLING_TEMPERATURE − 5 К восстановление не происходит; '
			'после снижения ниже неё через 30 секунд появляется информационная запись '
			'устранения перегрева. Отдельные результаты пунктов; преждевременные записи недопустимы.')

	def get_checklist_id(self):
		return '9.21, 9.22'

	def run(self):
		self.run_overheat_test()
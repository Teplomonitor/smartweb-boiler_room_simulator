from scenario.base.snowmelter_priority import SnowmelterPriorityScenario


class Scenario(SnowmelterPriorityScenario):
	def get_scenario_title(self):
		return 'Snowmelter priority request - flow temperature deficit'

	def get_scenario_description(self):
		return ('Снеготайка не отправляет GIVE_WAY при недогреве подачи ровно 5 °C '
			'и включает запрос приоритета при недогреве более 5 °C')

	def get_checklist_id(self):
		return '5.1.2.1'

	def run(self):
		self._run_priority_test()
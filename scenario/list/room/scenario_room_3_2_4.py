from scenario.base.room import RoomScenario


class Scenario(RoomScenario):
	ESTIMATED_RUN_SECONDS = 110

	def get_checklist_id(self):
		return '3.2.4'

	def get_scenario_title(self):
		return 'Комната: групповая смена режима'

	def get_scenario_description(self):
		return (
			'Прямая групповая CAN-команда меняет режим всех трёх комнат заданной группы. '
			'Проверяются комфортный, экономичный, автоматический и выключенный режимы. '
			'Режим контрольной комнаты другой группы не меняется.'
		)

	def run(self):
		self._run_test(lambda: self._group_sequence(broadcast=True))

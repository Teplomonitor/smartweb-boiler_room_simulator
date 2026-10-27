from scenario.base.room import RoomScenario


class Scenario(RoomScenario):
	def get_checklist_id(self):
		return '3.2.3'

	def get_scenario_title(self):
		return 'Комната: распространение режима внутри группы'

	def get_scenario_description(self):
		return (
			'При изменении режима каждой из трёх комнат тот же режим появляется у остальных '
			'комнат общей группы. Проверяются все четыре режима; комната другой группы не меняется.'
		)

	def run(self):
		self._run_test(lambda: self._group_sequence(broadcast=False))

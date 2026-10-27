from scenario.base.room import RoomScenario


class Scenario(RoomScenario):
	TEST_SCHEDULE = True

	def get_checklist_id(self):
		return '3.2.2'

	def get_scenario_title(self):
		return 'Комната: требуемая температура и расписание'

	def get_scenario_description(self):
		return (
			'Проверка комфортной, экономичной и выключенной уставок. В автоматическом режиме '
			'проверяются переходы экономичный → комфортный → экономичный по расписанию, '
			'построенному по текущим дате, дню недели и времени контроллера без изменения его часов.'
		)

	def run(self):
		self._run_test(self._temperature_sequence)

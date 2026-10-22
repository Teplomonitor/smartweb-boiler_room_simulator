from scenario.base.cascade_dispatch import CascadeDispatchScenario


class Scenario(CascadeDispatchScenario):
	BOILER_COUNT = 3
	DELAY_MINUTES = 1

	def get_checklist_id(self):
		return '3.6.3.5'

	def get_default_preset(self):
		return 'cascade_manager_3_boilers'

	def get_scenario_title(self):
		return 'Cascade: 3 boilers, stage delay and cancellation'

	def get_scenario_description(self):
		return 'Три котла: задержка следующей ступени 1 минута, отмена запроса, сброс таймера и повторный пуск.'

	def run(self):
		self._status = 'FAIL'
		self.execute()
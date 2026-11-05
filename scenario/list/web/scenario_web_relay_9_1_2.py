from scenario.base.web_bindings import WebBindingScenario


class Scenario(WebBindingScenario):
	ESTIMATED_RUN_SECONDS = 120
	REQUIRED_RELAY_COUNT = 1

	def get_scenario_title(self):
		return 'Web: привязка реле контроллера'

	def get_scenario_description(self):
		return 'Привязка, повтор, перепривязка и двойная отвязка реле; проверка прямых и обратных связей через CAN'

	def get_checklist_id(self):
		return '9.1.2'

	def run(self):
		self.run_binding_test(self.check_relay_sequence)
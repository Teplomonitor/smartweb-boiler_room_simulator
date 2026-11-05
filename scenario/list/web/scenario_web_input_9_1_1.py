from scenario.base.web_bindings import WebBindingScenario


class Scenario(WebBindingScenario):
	ESTIMATED_RUN_SECONDS = 120
	REQUIRED_INPUT_COUNT = 2

	def get_scenario_title(self):
		return 'Web: привязка входа программы'

	def get_scenario_description(self):
		return 'Привязка, повтор, перепривязка и двойная отвязка локального входа; проверка через CAN'

	def get_checklist_id(self):
		return '9.1.1'

	def run(self):
		self.run_binding_test(self.check_input_sequence)
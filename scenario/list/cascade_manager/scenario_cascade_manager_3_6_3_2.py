from scenario.base.cascade_dispatch import CascadeDispatchScenario


class Scenario(CascadeDispatchScenario):
	BOILER_COUNT = 3

	def get_checklist_id(self):
		return '3.6.3.2'

	def get_default_preset(self):
		return 'cascade_manager_3_boilers'

	def get_scenario_title(self):
		return 'Cascade: 3 boilers, no stage delay'

	def get_scenario_description(self):
		return 'Три котла: команды, выходы, рост и снижение нагрузки, останов и повторный пуск без задержки.'

	def run(self):
		self._status = 'FAIL'
		self.execute()
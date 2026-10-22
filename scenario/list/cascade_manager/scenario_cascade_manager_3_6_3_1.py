from scenario.base.cascade_dispatch import CascadeDispatchScenario


class Scenario(CascadeDispatchScenario):
	BOILER_COUNT = 2

	def get_checklist_id(self):
		return '3.6.3.1'

	def get_default_preset(self):
		return 'cascade_manager_2_boilers'

	def get_scenario_title(self):
		return 'Cascade: 2 boilers, no stage delay'

	def get_scenario_description(self):
		return 'Два котла: команды, выходы, рост и снижение нагрузки, останов и повторный пуск без задержки.'

	def run(self):
		self._status = 'FAIL'
		self.execute()
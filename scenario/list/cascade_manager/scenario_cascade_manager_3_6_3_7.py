from scenario.base.cascade_dispatch import CascadeDispatchScenario


class Scenario(CascadeDispatchScenario):
	BOILER_COUNT = 2
	TEST_FAULTS = True

	def get_checklist_id(self):
		return '3.6.3.7'

	def get_default_preset(self):
		return 'cascade_manager_2_boilers'

	def get_scenario_title(self):
		return 'Cascade: 2 boilers, faults and recovery, no delay'

	def get_scenario_description(self):
		return 'Два котла: аварии до пуска и в работе, нулевые команды неисправным, замещение и восстановление.'

	def run(self):
		self._status = 'FAIL'
		self.execute()
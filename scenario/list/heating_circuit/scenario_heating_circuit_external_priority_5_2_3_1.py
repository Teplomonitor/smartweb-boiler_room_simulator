from scenario.base.external_priority import ExternalPriorityScenario


class Scenario(ExternalPriorityScenario):
	TARGET = 'mixed'
	PRESET = 'heating_circuit_external_priority'

	def get_scenario_title(self):
		return 'Mixed circuit - pump stops when external priority delta exceeds 3'

	def get_scenario_description(self):
		return 'При управлении смесителем насос работает при разнице 3 и выключается при разнице 4'

	def get_checklist_id(self):
		return '5.2.3.1'

	def run(self):
		self._run_external_test('pump')
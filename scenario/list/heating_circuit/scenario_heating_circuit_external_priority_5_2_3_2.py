from scenario.base.external_priority import ExternalPriorityScenario


class Scenario(ExternalPriorityScenario):
	TARGET = 'direct'
	PRESET = 'heating_circuit_external_priority'

	def get_scenario_title(self):
		return 'Direct circuit - pump stops when external priority delta exceeds 0'

	def get_scenario_description(self):
		return 'Без управления смесителем насос работает при разнице 0 и выключается при разнице 1'

	def get_checklist_id(self):
		return '5.2.3.2'

	def run(self):
		self._run_external_test('pump')
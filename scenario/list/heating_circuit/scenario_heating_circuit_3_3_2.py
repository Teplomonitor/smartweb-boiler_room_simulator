from scenario.base.heating_circuit_mixer import HeatingCircuitMixerScenario


class Scenario(HeatingCircuitMixerScenario):
	def get_checklist_id(self):
		return '3.3.2'

	def get_default_preset(self):
		return 'heating_circuit_3_3_2'

	def get_scenario_title(self):
		return 'Heating circuit: analog mixer temperature control'

	def get_scenario_description(self):
		return super().get_scenario_description()

	def run(self):
		self._run_test()
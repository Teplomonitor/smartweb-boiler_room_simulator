from scenario.base.heating_circuit_priority import HeatingCircuitPriorityScenario


class Scenario(HeatingCircuitPriorityScenario):
	def get_scenario_title(self):
		return 'Heating circuit priority request - no flow sensor'

	def get_scenario_description(self):
		return ('Прямой контур и смесительный контур без датчика подачи не отправляют '
			'GIVE_WAY при активном запросе тепла; смесительный контур с датчиком служит контролем')

	def get_checklist_id(self):
		return '5.1.3.2'

	def run(self):
		self._run_priority_test(without_sensor=True)
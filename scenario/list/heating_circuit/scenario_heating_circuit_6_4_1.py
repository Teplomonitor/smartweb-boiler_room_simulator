from scenario.base.heat_dump import HeatDumpScenario


class Scenario(HeatDumpScenario):
	def get_scenario_title(self):
		return '6.4.1 Отопительный контур: циркуляционный насос'

	def get_scenario_description(self):
		return 'Сброс тепла включает насос контура вопреки режиму выключенного насоса'

	def get_checklist_id(self):
		return '6.4.1'

	def run(self):
		circuit = self._programList['circuit']
		pump = circuit.get_output_channel('pump')
		def baseline():
			self.expect(pump, self.RELAY_OFF, 'Насос контура до сброса')
		def active():
			self.expect(pump, lambda value: value != self.RELAY_OFF, 'Насос отопительного контура')
		self.run_heat_dump(self.circuit_settings(),
			[(circuit.get_input_channel('temperature'), 30)], baseline, active)
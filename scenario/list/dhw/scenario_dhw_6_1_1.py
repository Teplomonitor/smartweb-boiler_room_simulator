from scenario.base.heat_dump import HeatDumpScenario
import smartnet.constants as snc


class Scenario(HeatDumpScenario):
	def get_scenario_title(self):
		return '6.1.1 ГВС: насос загрузки на максимальной мощности'

	def get_scenario_description(self):
		return 'При разрешённом сбросе тепла включает насос ГВС с максимальным аналоговым сигналом'

	def get_checklist_id(self):
		return '6.1.1'

	def run(self):
		dhw = self._programList['dhw']
		pump = dhw.get_supply_pump_state()
		analog = dhw.get_output_channel('analogLoadingPump')
		settings = self.consumer_settings('dhw') + [
			self.setting('dhw', snc.ProgramType.DHW, snc.DhwParameterId.WORK_MODE, 0),
			self.setting('dhw', snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT, 45),
			self.setting('dhw', snc.ProgramType.DHW, snc.DhwParameterId.DHW_RELIEF, 0),
		]
		def baseline():
			self.expect(pump, self.RELAY_OFF, 'Насос ГВС до сброса')
			self.expect(analog, self.RELAY_OFF, 'Аналоговый насос ГВС до сброса')
		def active():
			self.expect(pump, lambda value: value != self.RELAY_OFF, 'Насос ГВС')
			self.expect(analog, self.RELAY_MAX, 'Максимальный сигнал насоса ГВС')
		self.run_heat_dump(settings, [(dhw.get_temperature(), 70)], baseline, active)
from scenario.base.heat_dump import HeatDumpScenario
import smartnet.constants as snc


class Scenario(HeatDumpScenario):
	def get_scenario_title(self):
		return '6.2.1 Снеготайка: насос загрузки на полной мощности'

	def get_scenario_description(self):
		return 'Сброс тепла включает загрузочный насос снеготайки с максимальным аналоговым сигналом'

	def get_checklist_id(self):
		return '6.2.1'

	def run(self):
		snow = self._programList['snow']
		pump = snow.getPrimaryPumpState()
		analog = snow.getAnalogPumpSignal()
		settings = self.consumer_settings('snow') + [
			self.setting('snow', snc.ProgramType.SNOWMELT, snc.SnowMelterParameterId.WORK_MODE, 0),
		]
		sensors = [(snow.getDirectFlowTemperature(), 35),
			(snow.getBackwardFlowTemperature(), 35), (snow.getPlateTemperature(), 0)]
		def baseline():
			self.expect(pump, self.RELAY_OFF, 'Насос загрузки до сброса')
			self.expect(analog, self.RELAY_OFF, 'Аналоговый насос до сброса')
		def active():
			self.expect(pump, lambda value: value != self.RELAY_OFF, 'Насос загрузки снеготайки')
			self.expect(analog, self.RELAY_MAX, 'Максимальный сигнал снеготайки')
		self.run_heat_dump(settings, sensors, baseline, active)
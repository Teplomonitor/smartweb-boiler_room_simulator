from scenario.base.heat_dump import HeatDumpScenario
import smartnet.constants as snc


class Scenario(HeatDumpScenario):
	def get_scenario_title(self):
		return '6.2.2 Снеготайка: циркуляционный насос'

	def get_scenario_description(self):
		return 'При разрешённом сбросе тепла включает циркуляцию снеготайки'

	def get_checklist_id(self):
		return '6.2.2'

	def run(self):
		snow = self._programList['snow']
		pump = snow.getSecondaryPumpState()
		settings = self.consumer_settings('snow') + [
			self.setting('snow', snc.ProgramType.SNOWMELT, snc.SnowMelterParameterId.WORK_MODE, 0),
		]
		sensors = [(snow.getDirectFlowTemperature(), 35),
			(snow.getBackwardFlowTemperature(), 35), (snow.getPlateTemperature(), 0)]
		def baseline():
			self.expect(pump, self.RELAY_OFF, 'Циркуляция снеготайки до сброса')
		def active():
			self.expect(pump, lambda value: value != self.RELAY_OFF, 'Циркуляция снеготайки')
		self.run_heat_dump(settings, sensors, baseline, active)
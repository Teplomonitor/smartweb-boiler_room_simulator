from scenario.base.heat_dump import HeatDumpScenario
import smartnet.constants as snc


class Scenario(HeatDumpScenario):
	def get_scenario_title(self):
		return '6.3.1 Бассейн: загрузочный насос'

	def get_scenario_description(self):
		return 'Сброс тепла включает насос загрузки бассейна даже при горячей воде'

	def get_checklist_id(self):
		return '6.3.1'

	def run(self):
		pool = self._programList['pool']
		pump = pool.getLoadingPumpState()
		settings = self.consumer_settings('pool') + [
			self.setting('pool', snc.ProgramType.POOL, snc.SwimmingPoolParameterId.WORK_MODE, 0),
			self.setting('pool', snc.ProgramType.POOL, snc.SwimmingPoolParameterId.REQUIRED_POOL_TEMPERATURE, 28),
			self.setting('pool', snc.ProgramType.POOL, snc.SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_MODE, 3),
		]
		def baseline():
			self.expect(pump, self.RELAY_OFF, 'Насос загрузки бассейна до сброса')
		def active():
			self.expect(pump, lambda value: value != self.RELAY_OFF, 'Насос загрузки бассейна')
		self.run_heat_dump(settings, [(pool.get_temperature(), 40)], baseline, active)
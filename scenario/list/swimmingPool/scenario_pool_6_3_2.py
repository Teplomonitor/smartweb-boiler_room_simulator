from scenario.base.heat_dump import HeatDumpScenario
import smartnet.constants as snc


class Scenario(HeatDumpScenario):
	def get_scenario_title(self):
		return '6.3.2 Бассейн: циркуляционный насос'

	def get_scenario_description(self):
		return 'Сброс тепла включает циркуляцию бассейна в режиме выключенной циркуляции'

	def get_checklist_id(self):
		return '6.3.2'

	def run(self):
		pool = self._programList['pool']
		pump = pool.getCirculationPumpState()
		settings = self.consumer_settings('pool') + [
			self.setting('pool', snc.ProgramType.POOL, snc.SwimmingPoolParameterId.WORK_MODE, 0),
			self.setting('pool', snc.ProgramType.POOL, snc.SwimmingPoolParameterId.REQUIRED_POOL_TEMPERATURE, 28),
			self.setting('pool', snc.ProgramType.POOL, snc.SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_MODE, 3),
		]
		def baseline():
			self.expect(pump, self.RELAY_OFF, 'Циркуляция бассейна до сброса')
		def active():
			self.expect(pump, lambda value: value != self.RELAY_OFF, 'Циркуляция бассейна')
		self.run_heat_dump(settings, [(pool.get_temperature(), 40)], baseline, active)
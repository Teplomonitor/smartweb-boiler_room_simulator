from scenario.base.journal_boiler_warmup import JournalBoilerWarmupScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalBoilerWarmupScenario):
	def get_scenario_title(self):
		return 'Journal: boiler warm-up starts'

	def get_scenario_description(self):
		return 'При работе котла ниже температуры разогрева появляется запись о начале прогрева'

	def get_checklist_id(self):
		return '9.6'

	def run(self):
		self._status = 'FAIL'
		try:
			if not self.prepare_boiler_warmup() or not self.snapshot_journal():
				return
			self.set_sensor_value(self._boiler_sensor, self.cold_temperature())
			if self.wait_journal_entry(
				MessageLogCode.MLC_BOILER_WARM_UP_STARTED,
				SeverityCode.SC_NOTICE,
				self._boiler.get_id(),
				self.WARMUP_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			self.finish_boiler_warmup()
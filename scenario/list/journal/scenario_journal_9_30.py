from scenario.base.journal_pool_flow import JournalPoolFlowScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalPoolFlowScenario):
	def get_scenario_title(self):
		return 'Journal: pool circulation restored'

	def get_scenario_description(self):
		return 'После аварии циркуляции восстановление протока отмечается в журнале'

	def get_checklist_id(self):
		return '9.30'

	def run(self):
		self._status = 'FAIL'
		try:
			if not self.prepare_pool_flow() or not self.snapshot_journal():
				return
			self.set_sensor_value(self._flow_sensor, 'open')
			if not self.wait_journal_entry(
				MessageLogCode.MLC_CIRCULATION_ERROR,
				SeverityCode.SC_CRITICAL,
				self._pool.get_id(),
				self.FLOW_ALARM_TIMEOUT,
			):
				return
			if not self.snapshot_journal():
				return
			self.set_sensor_value(self._flow_sensor, 'short')
			if self.wait_journal_entry(
				MessageLogCode.MLC_CIRCULATION_NO_ERROR,
				SeverityCode.SC_NOTICE,
				self._pool.get_id(),
				self.FLOW_RECOVERY_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			self.finish_pool_flow()
from consoleLog import print_error
from scenario.base.journal_pool_flow import JournalPoolFlowScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalPoolFlowScenario):
	def get_scenario_title(self):
		return 'Journal: pool circulation lost'

	def get_scenario_description(self):
		return 'При работе циркуляционного насоса без протока в журнале появляется авария'

	def get_checklist_id(self):
		return '9.29'

	def run(self):
		self._status = 'FAIL'
		try:
			if not self.prepare_pool_flow() or not self.snapshot_journal():
				return
			self.set_sensor_value(self._flow_sensor, 'open')
			if not self.wait_event(self.circulation_pump_is_on, self.PUMP_START_TIMEOUT):
				print_error('Насос выключился до проверки отсутствия протока')
				return
			if self.wait_journal_entry(
				MessageLogCode.MLC_CIRCULATION_ERROR,
				SeverityCode.SC_CRITICAL,
				self._pool.get_id(),
				self.FLOW_ALARM_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			self.finish_pool_flow()
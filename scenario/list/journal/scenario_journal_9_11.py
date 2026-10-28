from consoleLog import print_error
from scenario.base.journal import JournalFillingLoopScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalFillingLoopScenario):
	def get_scenario_title(self):
		return 'Journal: low pressure alarm'

	def get_scenario_description(self):
		return 'При длительном низком давлении появляется аварийная запись журнала'

	def get_checklist_id(self):
		return '9.11'

	def run(self):
		self._status = 'FAIL'
		try:
			if not self.prepare_journal_test(short_alarm=True):
				print_error('Не удалось подготовить проверку подпитки')
				return
			if not self.snapshot_journal() or not self.set_low_pressure():
				return
			if not self.wait_event(self.alarm_is_on, self.SHORT_ALARM_DURATION + self.ALARM_TIMEOUT_MARGIN):
				print_error('Авария низкого давления не включилась')
				return
			if self.wait_journal_entry(
				MessageLogCode.MLC_LOW_PRESSURE_ALARM_STARTED,
				SeverityCode.SC_CRITICAL,
				self._filling_loop.get_id(),
				self.EVENT_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			self.finish_journal_test()
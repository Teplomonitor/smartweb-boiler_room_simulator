from consoleLog import print_error
from scenario.base.journal import JournalFillingLoopScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalFillingLoopScenario):
	def get_scenario_title(self):
		return 'Journal: automatic filling starts'

	def get_scenario_description(self):
		return 'При запуске автоподпитки в журнале появляется информационная запись'

	def get_checklist_id(self):
		return '9.13'

	def run(self):
		self._status = 'FAIL'
		try:
			if not self.prepare_journal_test():
				print_error('Не удалось подготовить проверку подпитки')
				return
			if not self.snapshot_journal():
				return
			if not self.write_parameter('autoFill', 1) or not self.set_low_pressure():
				print_error('Не удалось включить автоматическую подпитку')
				return
			if not self.wait_event(self.filling_is_on, self.EVENT_TIMEOUT):
				print_error('Автоподпитка не включилась')
				return
			if self.wait_journal_entry(
				MessageLogCode.MLC_FL_AUTO_FILL_STARTED,
				SeverityCode.SC_NOTICE,
				self._filling_loop.get_id(),
				self.EVENT_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			self.finish_journal_test()
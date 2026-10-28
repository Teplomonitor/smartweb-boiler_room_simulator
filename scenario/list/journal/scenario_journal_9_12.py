from consoleLog import print_error
from scenario.base.journal import JournalFillingLoopScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalFillingLoopScenario):
	def get_scenario_title(self):
		return 'Journal: pressure returns to normal'

	def get_scenario_description(self):
		return 'После аварии давление восстанавливается и в журнале появляется запись об этом'

	def get_checklist_id(self):
		return '9.12'

	def run(self):
		self._status = 'FAIL'
		try:
			if not self.prepare_journal_test(short_alarm=True) or not self.set_low_pressure():
				print_error('Не удалось подготовить аварийное состояние подпитки')
				return
			if not self.wait_event(self.alarm_is_on, self.SHORT_ALARM_DURATION + self.ALARM_TIMEOUT_MARGIN):
				print_error('Не возникла исходная авария низкого давления')
				return
			if not self.snapshot_journal() or not self.set_normal_pressure():
				return
			if not self.wait_event(self.alarm_is_off, self.EVENT_TIMEOUT):
				print_error('Авария не снялась после нормализации давления')
				return
			if self.wait_journal_entry(
				MessageLogCode.MLC_LOW_PRESSURE_ALARM_ENDED,
				SeverityCode.SC_NOTICE,
				self._filling_loop.get_id(),
				self.EVENT_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			self.finish_journal_test()
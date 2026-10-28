from consoleLog import print_error
from scenario.base.journal_alarm import JournalAlarmScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalAlarmScenario):
	def get_scenario_title(self):
		return 'Journal: alarm input reset manually'

	def get_scenario_description(self):
		return 'После окончания условия аварии вход сигнализации сбрасывается индивидуальной командой'

	def get_checklist_id(self):
		return '9.10'

	def run(self):
		self._status = 'FAIL'
		try:
			if not self.prepare_alarm(auto_reset=False) or not self.start_alarm():
				return
			self.set_sensor_value(self._alarm_sensor, 'open')
			self.wait(self.SETTLE_TIME)
			if not self.snapshot_journal():
				return
			if not self._alarm.reset_alarm_input(self.INPUT_INDEX):
				print_error('Индивидуальный сброс аварии не выполнен')
				return
			self._alarm_needs_reset = False
			if self.wait_journal_entry(
				MessageLogCode.MLC_ALARM_RESET, SeverityCode.SC_NOTICE,
				self._alarm.get_id(), self.ALARM_TIMEOUT, param_ex=[self.INPUT_INDEX],
			):
				self._status = 'OK'
		finally:
			self.finish_alarm()
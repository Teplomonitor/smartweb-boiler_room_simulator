from scenario.base.journal_alarm import JournalAlarmScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalAlarmScenario):
	def get_scenario_title(self):
		return 'Journal: alarm input condition ended'

	def get_scenario_description(self):
		return 'Когда условие аварии на входе сигнализации исчезает, в журнале появляется запись о снятии аварии'

	def get_checklist_id(self):
		return '9.9'

	def run(self):
		self._status = 'FAIL'
		try:
			if not self.prepare_alarm(auto_reset=True) or not self.start_alarm():
				return
			if not self.snapshot_journal():
				return
			self.set_sensor_value(self._alarm_sensor, 'open')
			if self.wait_journal_entry(
				MessageLogCode.MLC_ALARM_ENDED, SeverityCode.SC_WARNING,
				self._alarm.get_id(), self.ALARM_TIMEOUT, param_ex=[self.INPUT_INDEX],
			):
				self._status = 'OK'
		finally:
			self.finish_alarm()
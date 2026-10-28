from scenario.base.journal_dhw_disinfection import JournalDhwDisinfectionScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalDhwDisinfectionScenario):
	def get_scenario_title(self):
		return 'Journal: DHW disinfection ends'

	def get_scenario_description(self):
		return 'Режим дезинфекции ГВС заканчивается после реального часового цикла'

	def get_checklist_id(self):
		return '9.5'

	def run(self):
		self._status = 'FAIL'
		try:
			if not self.prepare_disinfection():
				return
			if not self.wait_journal_entry(
				MessageLogCode.MLC_ANTILEGION_PROTECTION_STARTED,
				SeverityCode.SC_NOTICE, 0, self.START_TIMEOUT,
			):
				return
			if not self.snapshot_journal():
				return
			if self.wait_journal_entry(
				MessageLogCode.MLC_ANTILEGION_PROTECTION_ENDED,
				SeverityCode.SC_NOTICE, 0, self.END_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			self.finish_disinfection()
from scenario.base.journal_dhw_disinfection import JournalDhwDisinfectionScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalDhwDisinfectionScenario):
	def get_scenario_title(self):
		return 'Journal: DHW disinfection starts'

	def get_scenario_description(self):
		return 'После перехода на понедельник контроллер сообщает о начале дезинфекции ГВС'

	def get_checklist_id(self):
		return '9.4'

	def run(self):
		self._status = 'FAIL'
		try:
			if not self.prepare_disinfection():
				return
			if self.wait_journal_entry(
				MessageLogCode.MLC_ANTILEGION_PROTECTION_STARTED,
				SeverityCode.SC_NOTICE, 0, self.START_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			self.finish_disinfection()
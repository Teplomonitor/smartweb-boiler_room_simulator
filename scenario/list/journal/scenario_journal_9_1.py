from scenario.base.journal_collision import JournalCollisionScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalCollisionScenario):
	def get_scenario_title(self):
		return 'Journal: program ID collision'

	def get_scenario_description(self):
		return 'Совпадение номера двух программ приводит к записи коллизии CID/PID'

	def get_checklist_id(self):
		return '9.1'

	def run(self):
		self._status = 'FAIL'
		self.wait(self.QUIET_PERIOD)
		if not self.snapshot_journal():
			return
		program_id = self._programList['boiler'].get_id()
		controller_id = self._controllerHost.get_controller_id()
		emitter = self.make_collision_emitter()
		try:
			emitter.start()
			if self.wait_journal_entry(
				MessageLogCode.MLC_CONTROLLER_ERROR,
				SeverityCode.SC_ALERT, 0, self.JOURNAL_TIMEOUT,
				param_ex=[controller_id, program_id],
			):
				self._status = 'OK'
		finally:
			emitter.stop()
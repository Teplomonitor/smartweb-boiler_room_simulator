from consoleLog import print_error
from scenario.base.journal import JournalCanEmitter, JournalScenarioMixin
from scenario.scenario import Scenario as Parent
from smartnet.message import Message
from smartnet.message_log_constants import MessageLogCode, SeverityCode
import smartnet.constants as snc


class Scenario(JournalScenarioMixin, Parent):
	JOURNAL_TIMEOUT = 45
	SECOND_OUTDOOR_ID = 102

	def get_scenario_title(self):
		return 'Journal: multiple outdoor sensors'

	def get_scenario_description(self):
		return 'Ответы второго уличного датчика по CAN создают запись о нескольких датчиках'

	def get_checklist_id(self):
		return '9.3'

	def get_required_programs(self):
		return {'outdoor': snc.ProgramType.OUTDOOR_SENSOR}

	def get_default_preset(self):
		return 'journal_outdoor'

	def force_preset_load(self):
		return True

	def run(self):
		self._status = 'FAIL'
		if self._programList['outdoor'].get_id() == self.SECOND_OUTDOOR_ID:
			print_error('Номер второго уличного датчика совпадает с основным')
			return
		if not self.snapshot_journal():
			return

		response = Message(
			snc.ProgramType.OUTDOOR_SENSOR, self.SECOND_OUTDOOR_ID,
			snc.OutdoorSensorFunction.GET_TEMPERATURE, snc.RequestFlag.RESPONSE,
			[0, 0],
		)
		emitter = JournalCanEmitter([response])
		try:
			emitter.start()
			if self.wait_journal_entry(
				MessageLogCode.MLC_MORE_THEN_ONE_OUTDOOR_SENSOR,
				SeverityCode.SC_ERROR, 0, self.JOURNAL_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			emitter.stop()
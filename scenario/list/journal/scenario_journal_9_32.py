from consoleLog import print_error
from scenario.base.journal import JournalScenarioMixin
from scenario.scenario import Scenario as Parent
from smartnet.message_log_constants import MessageLogCode, SeverityCode
import smartnet.constants as snc


class Scenario(JournalScenarioMixin, Parent):
	INITIAL_STATE_DELAY = 12
	ALARM_TIMEOUT = 50

	def get_scenario_title(self):
		return 'Journal: boiler error input'

	def get_scenario_description(self):
		return 'Замыкание входа ошибки котла создаёт запись об ошибке в журнале'

	def get_checklist_id(self):
		return '9.32'

	def get_required_programs(self):
		return {'boiler': snc.ProgramType.BOILER}

	def get_default_preset(self):
		return 'boiler_journal_error'

	def force_preset_load(self):
		return True

	def run(self):
		self._status = 'FAIL'
		boiler = self._programList['boiler']
		sensor = boiler.get_input_channel('error')
		if sensor is None or not sensor.is_mapped():
			print_error('Вход ошибки котла не привязан к датчику')
			return

		try:
			self.set_sensor_value(sensor, 'open')
			self.wait(self.INITIAL_STATE_DELAY)
			if not self.snapshot_journal():
				return
			self.set_sensor_value(sensor, 'short')
			if self.wait_journal_entry(
				MessageLogCode.MLC_BOILER_ERROR,
				SeverityCode.SC_WARNING,
				boiler.get_id(),
				self.ALARM_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			self.set_sensor_value(sensor, 'open')
			sensor.set_manual(False)
from consoleLog import print_error
from scenario.base.journal import JournalScenarioMixin
from scenario.base.swimming_pool import PoolScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalScenarioMixin, PoolScenario):
	FILLING_DURATION = 60
	REFILL_TIMEOUT = 30
	ALARM_TIMEOUT_MARGIN = 45
	JOURNAL_TIMEOUT = 30

	def get_scenario_title(self):
		return 'Journal: pool low water level'

	def get_scenario_description(self):
		return 'После длительной подпитки бассейна в журнале появляется авария низкого уровня воды'

	def get_checklist_id(self):
		return '9.28'

	def get_default_preset(self):
		return 'swimmingPool_with_level'

	def force_preset_load(self):
		return True

	def run(self):
		self._status = 'FAIL'
		pool = self._pool
		sensor = pool.get_input_channel('waterLevel')
		original_duration = pool.read_parameter_value('fillingDuration')
		if original_duration is None or sensor is None or not sensor.is_mapped():
			print_error('Недоступен датчик уровня воды или длительность подпитки')
			return

		try:
			self.set_sensor_value(sensor, 'short')
			if pool.resetWaterLevelAlarm() is None:
				print_error('Не удалось сбросить аварию уровня воды')
				return
			if pool.write_parameter_value('fillingDuration', self.FILLING_DURATION) is None:
				print_error('Не удалось задать время подпитки')
				return
			if not self.wait_event(
				lambda: pool.get_output_channel('waterLevelControl').get_value() == self.RELAY_OFF,
				self.REFILL_TIMEOUT,
			):
				print_error('Подпитка не отключилась при нормальном уровне воды')
				return
			if not self.snapshot_journal():
				return
			self.set_sensor_value(sensor, 'open')
			if not self.wait_event(
				lambda: pool.get_output_channel('waterLevelControl').get_value() != self.RELAY_OFF,
				self.REFILL_TIMEOUT,
			):
				print_error('Подпитка не включилась при низком уровне воды')
				return
			if self.wait_journal_entry(
				MessageLogCode.MLC_LOW_POOL_WATER_LEVEL,
				SeverityCode.SC_CRITICAL,
				pool.get_id(),
				self.FILLING_DURATION + self.ALARM_TIMEOUT_MARGIN + self.JOURNAL_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			self.set_sensor_value(sensor, 'short')
			sensor.set_manual(False)
			if pool.write_parameter_value('fillingDuration', original_duration) is None:
				print_error('Не удалось восстановить время подпитки бассейна')
				self._status = 'FAIL'
			if pool.resetWaterLevelAlarm() is None:
				print_error('Не удалось сбросить аварию уровня воды после теста')
				self._status = 'FAIL'
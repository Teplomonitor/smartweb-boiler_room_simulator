from consoleLog import print_error
from scenario.base.journal import JournalScenarioMixin
from scenario.scenario import Scenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode
import smartnet.constants as snc


class JournalAlarmScenario(JournalScenarioMixin, Scenario):
	INPUT_INDEX = 0
	INPUT_TYPE_SHORTABLE = 2
	ALARM_DELAY = 1  # seconds; remote-control TIME_MS is converted by the protocol layer
	SETTLE_TIME = 3
	ALARM_TIMEOUT = 30

	def get_required_programs(self):
		return {'alarm': snc.ProgramType.ALARM}

	def get_default_preset(self):
		return 'alarm'

	def force_preset_load(self):
		return True

	def prepare_alarm(self, auto_reset):
		self._alarm = self._programList['alarm']
		self._alarm_sensor = self._alarm.get_alarm_input(self.INPUT_INDEX)
		self._original_alarm_parameters = {}
		self._alarm_needs_reset = not auto_reset
		self._alarm_sensor_controlled = False
		if self._alarm_sensor is None or not self._alarm_sensor.is_mapped():
			print_error('Вход сигнализации не подключён')
			return False
		if self._alarm_sensor.isShort():
			print_error('Вход сигнализации уже замкнут: тест не может восстановить исходную аварию')
			return False
		self._original_sensor_value = (
			'open' if self._alarm_sensor.isOpen() else self._alarm_sensor.get_value()
		)
		for name in ('input_type', 'alarm_delay', 'auto_reset', 'enable_log'):
			value = self._alarm.read_parameter_value(name, index=self.INPUT_INDEX)
			if value is None:
				print_error(f'Не удалось прочитать параметр сигнализации {name}')
				return False
			self._original_alarm_parameters[name] = value

		self._alarm_sensor_controlled = True
		self.set_sensor_value(self._alarm_sensor, 'open')
		for name, value in (
			('input_type', self.INPUT_TYPE_SHORTABLE),
			('alarm_delay', self.ALARM_DELAY),
			('auto_reset', int(auto_reset)),
			('enable_log', 1),
		):
			if not self._alarm.write_parameter(name, value, index=self.INPUT_INDEX):
				print_error(f'Не удалось настроить параметр сигнализации {name}')
				return False
		self.wait(self.SETTLE_TIME)
		if not auto_reset and not self._alarm.reset_alarm_input(self.INPUT_INDEX):
			print_error('Не удалось очистить предыдущую аварию входа')
			return False
		return True

	def start_alarm(self):
		if not self.snapshot_journal():
			return False
		self.set_sensor_value(self._alarm_sensor, 'short')
		return self.wait_journal_entry(
			MessageLogCode.MLC_ALARM_STARTED, SeverityCode.SC_EMERGENCY,
			self._alarm.get_id(), self.ALARM_TIMEOUT, param_ex=[self.INPUT_INDEX],
		)

	def finish_alarm(self):
		if (not getattr(self, '_alarm_sensor_controlled', False)
				or not hasattr(self, '_alarm_sensor') or self._alarm_sensor is None):
			return
		# Remove the active condition before resetting a latched alarm.
		try:
			self.set_sensor_value(self._alarm_sensor, 'open')
			if getattr(self, '_original_alarm_parameters', None):
				self.simple_wait(self.SETTLE_TIME)
				if self._alarm_needs_reset and not self._alarm.reset_alarm_input(self.INPUT_INDEX):
					print_error('Не удалось снять тестовую аварию')
					self._status = 'FAIL'
				for name, value in self._original_alarm_parameters.items():
					if not self._alarm.write_parameter(name, value, index=self.INPUT_INDEX):
						print_error(f'Не удалось восстановить параметр сигнализации {name}')
						self._status = 'FAIL'
		finally:
			if hasattr(self, '_original_sensor_value') and self._original_sensor_value is not None:
				self.set_sensor_value(self._alarm_sensor, self._original_sensor_value)
			self._alarm_sensor.set_manual(False)
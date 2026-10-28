from consoleLog import print_error
from scenario.base.journal import JournalScenarioMixin
from scenario.base.swimming_pool import PoolScenario


class JournalPoolFlowScenario(JournalScenarioMixin, PoolScenario):
	POOL_WORK_MODE_COMFORT = 0
	CIRCULATION_WORK_MODE_ON = 0
	PUMP_START_TIMEOUT = 45
	FLOW_ALARM_TIMEOUT = 60
	FLOW_RECOVERY_TIMEOUT = 35

	def get_default_preset(self):
		return 'journal_pool_flow'

	def force_preset_load(self):
		return True

	def prepare_pool_flow(self):
		self._flow_sensor = self._pool.get_input_channel('flow')
		self._level_sensor = self._pool.get_input_channel('waterLevel')
		self._original_parameters = []
		if any(sensor is None or not sensor.is_mapped()
				for sensor in (self._flow_sensor, self._level_sensor)):
			print_error('Датчик протока или уровня воды не привязан')
			return False

		for parameter in ('workMode', 'circulationPumpWorkMode'):
			value = self._pool.read_parameter_value(parameter)
			if value is None:
				print_error(f'Не удалось прочитать настройку бассейна {parameter}')
				return False
			self._original_parameters.append((parameter, value))

		self.set_sensor_value(self._flow_sensor, 'short')
		self.set_sensor_value(self._level_sensor, 'short')
		if (self._pool.write_parameter_value('workMode', self.POOL_WORK_MODE_COMFORT) is None
				or self._pool.write_parameter_value('circulationPumpWorkMode', self.CIRCULATION_WORK_MODE_ON) is None):
			print_error('Не удалось включить постоянную циркуляцию бассейна')
			return False
		if not self.wait_event(self.circulation_pump_is_on, self.PUMP_START_TIMEOUT):
			print_error('Циркуляционный насос бассейна не включился')
			return False
		return True

	def finish_pool_flow(self):
		for sensor in (getattr(self, '_flow_sensor', None), getattr(self, '_level_sensor', None)):
			if sensor is not None and sensor.is_mapped():
				self.set_sensor_value(sensor, 'short')
				sensor.set_manual(False)
		for parameter, value in reversed(getattr(self, '_original_parameters', [])):
			if self._pool.write_parameter_value(parameter, value) is None:
				print_error(f'Не удалось восстановить настройку бассейна {parameter}')
				self._status = 'FAIL'
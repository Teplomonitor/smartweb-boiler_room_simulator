from consoleLog import print_error
from scenario.base.journal import JournalScenarioMixin
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
import smartnet.remoteControl as sr


class JournalBoilerWarmupScenario(JournalScenarioMixin, Parent):
	BURNER_TIMEOUT = 90
	WARMUP_TIMEOUT = 180
	WARMUP_OFFSET = 10
	DHW_SENSOR_TEMPERATURE = 20
	MINIMUM_DHW_SETPOINT = 60

	def get_required_programs(self):
		return {'boiler': snc.ProgramType.BOILER, 'dhw': snc.ProgramType.DHW}

	def get_default_preset(self):
		return 'boiler_3_5_2'

	def force_preset_load(self):
		return True

	def prepare_boiler_warmup(self):
		self._boiler = self._programList['boiler']
		self._dhw = self._programList['dhw']
		self._boiler_sensor = self._boiler.get_input_channel('temperature')
		self._dhw_sensor = self._dhw.get_temperature()
		burner = self._boiler.get_stage_1()
		self._initial_sensors = []
		self._initial_parameters = []
		for channel in (self._boiler_sensor, self._dhw_sensor, burner):
			if channel is None or not channel.is_mapped():
				print_error('Нет привязки датчика или первой ступени котла')
				return False

		for sensor in (self._boiler_sensor, self._dhw_sensor):
			value = sensor.get_value()
			if value is None:
				print_error('Не удалось получить исходную температуру')
				return False
			self._initial_sensors.append((sensor, value))

		warmup = sr.RemoteControlParameter(
			programType=snc.ProgramType.BOILER,
			parameterId=snc.BoilerParameterId.WARMUP_TEMPERATURE,
			programId=self._boiler.get_id(),
		)
		if not warmup.read():
			print_error('Не удалось прочитать порог прогрева котла')
			return False
		self._warmup_temperature = warmup.get_value()
		if (self._warmup_temperature is None
				or not 20 <= self._warmup_temperature <= 65):
			print_error('Порог прогрева котла вне тестового диапазона')
			return False

		for parameter in ('workMode', 'temperatureComfort'):
			value = self._dhw.read_parameter_value(parameter)
			if value is None:
				print_error(f'Не удалось прочитать настройку ГВС {parameter}')
				return False
			self._initial_parameters.append((parameter, value))

		self.set_sensor_value(self._dhw_sensor, self.DHW_SENSOR_TEMPERATURE)
		self.set_sensor_value(self._boiler_sensor, self.hot_temperature())
		if (self._dhw.write_parameter_value('workMode', 0) is None
				or self._dhw.write_parameter_value(
					'temperatureComfort',
					max(self.MINIMUM_DHW_SETPOINT, self._warmup_temperature + 2 * self.WARMUP_OFFSET),
				) is None):
			print_error('Не удалось включить запрос тепла от ГВС')
			return False

		if not self.wait_event(
			lambda: burner.get_value() is not None and burner.get_value() != self.RELAY_OFF,
			self.BURNER_TIMEOUT,
		):
			print_error('Первая ступень котла не включилась')
			return False
		return True

	def hot_temperature(self):
		return self._warmup_temperature + self.WARMUP_OFFSET

	def cold_temperature(self):
		return self._warmup_temperature - self.WARMUP_OFFSET

	def finish_boiler_warmup(self):
		for sensor, value in reversed(getattr(self, '_initial_sensors', [])):
			self.set_sensor_value(sensor, value)
			sensor.set_manual(False)
		for parameter, value in reversed(getattr(self, '_initial_parameters', [])):
			if self._dhw.write_parameter_value(parameter, value) is None:
				print_error(f'Не удалось восстановить настройку ГВС {parameter}')
				self._status = 'FAIL'
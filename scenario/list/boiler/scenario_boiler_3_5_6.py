from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
from scenario.base.filling_loop_signal import PRESSURE_INPUT_TYPE_RANGEABLE
import smartnet.constants as snc
import smartnet.remoteControl as sr


class Scenario(Parent):
	PRESSURE_NORMAL = 3
	PRESSURE_LOW = 0
	MINIMUM_PRESSURE = 1.5
	PRESSURE_HYSTERESIS = 0.3
	COLD_TEMPERATURE = 20
	DHW_COMFORT_TEMPERATURE = 60
	DHW_MODE_COMFORT = 0
	AUTO_FILL_OFF = 0
	FILLING_DURATION = 5
	STATE_TIMEOUT = 90
	RESTART_TIMEOUT = 180
	HOLD_DURATION = 5

	def get_scenario_title(self):
		return 'Boiler: shutdown on filling loop alarm and automatic recovery'

	def get_scenario_description(self):
		return (
			'Котёл выключает горелку и насос при аварии подпитки и возобновляет '
			'нагрев после нормализации давления при сохраняющемся запросе ГВС'
		)

	def get_checklist_id(self):
		return '3.5.6'

	def get_required_programs(self):
		return {
			'dhw': snc.ProgramType.DHW,
			'boiler': snc.ProgramType.BOILER,
			'filling_loop': snc.ProgramType.FILLING_LOOP,
		}

	def get_default_preset(self):
		return 'boiler_3_5_6'

	def force_preset_load(self):
		return True

	def _parameter(self, key, program_type, parameter_id):
		return program_type, parameter_id, self._programList[key].get_id()

	def _read_parameter(self, parameter):
		program_type, parameter_id, program_id = parameter
		remote = sr.RemoteControlParameter(
			programType=program_type, parameterId=parameter_id, programId=program_id,
		)
		return remote.get_value() if remote.read() else None

	def _write_parameter(self, parameter, value):
		program_type, parameter_id, program_id = parameter
		return sr.RemoteControlParameter(
			programType=program_type, parameterId=parameter_id, programId=program_id,
			parameterValue=value,
		).write()

	def _heat_is_requested(self):
		value = self._read_parameter(self._consumer_request)
		return value is not None and value > self.COLD_TEMPERATURE

	def _alarm_is(self, active):
		value = self._alarm.get_value()
		return value is not None and (value != self.RELAY_OFF) == active

	def _boiler_is(self, heating):
		stage_1, stage_2, pump = [channel.get_value() for channel in self._boiler_outputs]
		if heating:
			return stage_1 is not None and stage_1 != self.RELAY_OFF and pump == self.RELAY_ON
		return stage_1 == self.RELAY_OFF and stage_2 == self.RELAY_OFF and pump == self.RELAY_OFF

	def _check_state(self, alarm, heating, timeout, description):
		print_log(description)
		if not self.wait_state_permanence(
			lambda: self._alarm_is(alarm) and self._heat_is_requested() and self._boiler_is(heating),
			self.HOLD_DURATION,
			timeout,
		):
			print_error(f'Не подтверждено состояние: {description}')
			return False
		return True

	def run(self):
		self._status = 'FAIL'
		boiler = self._programList['boiler']
		dhw = self._programList['dhw']
		filling_loop = self._programList['filling_loop']
		pressure = filling_loop.getPressure()
		sensors = [pressure, boiler.get_input_channel('temperature'), dhw.get_temperature()]
		self._alarm = filling_loop.get_output_channel('alarm_output')
		self._boiler_outputs = [
			boiler.get_stage_1(), boiler.get_output_channel('burner2'), boiler.get_pump(),
		]
		for channel in sensors + self._boiler_outputs + [self._alarm]:
			if channel is None or not channel.is_mapped():
				print_error('Не привязан обязательный датчик или выход сценария 3.5.6')
				return
		initial_sensors = [(sensor, sensor.get_value(), sensor.isManual()) for sensor in sensors]
		if any(value is None for _, value, _ in initial_sensors):
			print_error('Не удалось прочитать исходные значения датчиков')
			return
		if initial_sensors[0][1] < self.PRESSURE_NORMAL:
			print_error('Исходное давление должно быть нормальным для безопасного восстановления')
			return

		self._consumer_request = self._parameter(
			'dhw', snc.ProgramType.CONSUMER, snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
		)
		settings = [
			('filling_loop', snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.AUTO_FILL, self.AUTO_FILL_OFF),
			('filling_loop', snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.PRESSURE_INPUT_TYPE, PRESSURE_INPUT_TYPE_RANGEABLE),
			('filling_loop', snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.MINIMUM_PRESSURE, self.MINIMUM_PRESSURE),
			('filling_loop', snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.PRESSURE_HYST, self.PRESSURE_HYSTERESIS),
			('filling_loop', snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.FILLING_DURATION, self.FILLING_DURATION),
			('dhw', snc.ProgramType.DHW, snc.DhwParameterId.WORK_MODE, self.DHW_MODE_COMFORT),
			('dhw', snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT, self.DHW_COMFORT_TEMPERATURE),
			('boiler', snc.ProgramType.TEMPERATURE_GENERATOR, snc.TemperatureGeneratorParameterId.MIN_OFF_TIME, 0),
		]
		parameters = []
		for key, program_type, parameter_id, test_value in settings:
			parameter = self._parameter(key, program_type, parameter_id)
			initial_value = self._read_parameter(parameter)
			if initial_value is None:
				print_error(f'Не удалось прочитать параметр {key}.{parameter_id}')
				return
			parameters.append((parameter, initial_value, test_value))

		modified_parameters = []
		try:
			for sensor, value in zip(sensors, (self.PRESSURE_NORMAL, self.COLD_TEMPERATURE, self.COLD_TEMPERATURE)):
				self.set_sensor_value(sensor, value)
			for parameter, initial_value, test_value in parameters:
				modified_parameters.append((parameter, initial_value))
				if not self._write_parameter(parameter, test_value):
					print_error('Не удалось настроить параметры сценария')
					return

			if not self._check_state(False, True, self.RESTART_TIMEOUT, 'Нормальное давление: котёл греет по запросу ГВС'):
				return
			self.set_sensor_value(pressure, self.PRESSURE_LOW)
			if not self._check_state(True, False, self.STATE_TIMEOUT, 'Низкое давление: авария подпитки выключает котёл'):
				return
			self.set_sensor_value(pressure, self.PRESSURE_NORMAL)
			if not self._check_state(False, True, self.RESTART_TIMEOUT, 'Давление восстановлено: котёл снова греет'):
				return
			self._status = 'OK'
		finally:
			# Remove the alarm while rangeable input and automatic reset are still configured.
			try:
				self.set_sensor_value(pressure, self.PRESSURE_NORMAL)
				if not self.wait_event(lambda: self._alarm_is(False), self.STATE_TIMEOUT):
					print_error('Не удалось снять аварию подпитки при завершении сценария')
					self._status = 'FAIL'
			except Exception as error:
				print_error(f'Ошибка снятия аварии подпитки: {error}')
				self._status = 'FAIL'
			for parameter, initial_value in reversed(modified_parameters):
				try:
					if not self._write_parameter(parameter, initial_value):
						raise RuntimeError('запись параметра не подтверждена')
				except Exception as error:
					print_error(f'Ошибка восстановления параметра: {error}')
					self._status = 'FAIL'
			for sensor, initial_value, initial_manual in initial_sensors:
				try:
					try:
						sensor.set_value(initial_value, True)
					finally:
						sensor.set_manual(initial_manual)
						if sensor in self._manualSensorsList:
							self._manualSensorsList.remove(sensor)
				except Exception as error:
					print_error(f'Ошибка восстановления датчика: {error}')
					self._status = 'FAIL'
		if self._status == 'OK':
			print_log('Котёл отключился по аварии и восстановил работу после нормализации давления')
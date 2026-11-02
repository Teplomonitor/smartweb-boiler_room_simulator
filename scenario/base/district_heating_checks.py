"""Deterministic inputs and transactional cleanup for district heating checks."""

from contextlib import contextmanager
import math
import time

from consoleLog import print_error, print_log
from scenario.base.district_heating import DistrictHeatingScenario
from scenario.base.filling_loop_signal import PRESSURE_INPUT_TYPE_OPENABLE


class CheckFailed(Exception):
	pass


class DistrictHeatingChecks(DistrictHeatingScenario):
	POLL_INTERVAL = 1
	STARTUP_TIMEOUT = 180
	LIMIT_TIMEOUT = 30
	VALVE_RUNNING_TIME = 30
	OPEN_VALVE_SIGNAL = 200
	CITY_SUPPLY = 80
	NORMAL_CITY_RETURN = 30
	NORMAL_HOUSE_RETURN = 30
	COLD_HOUSE_SUPPLY = 20
	TEMPERATURE_MARGIN = 5
	ALARM_FILLING_DURATION = 5
	ALARM_STATUS_TIMEOUT = 45
	ALARM_RESPONSE_TIMEOUT = 180
	ALARM_RESPONSE_STABILIZATION_DURATION = 30
	STARTUP_STABILIZATION_DURATION = 20
	MAXIMUM_ON_DELAY = 15 * 60
	ALARM_TEST_ON_DELAY = 15 * 60
	RETURN_LIMIT_DELAY = 60
	REVERSED_FLOW_DELAY = 120
	SLOW_CLOSING_FACTOR = 10
	MINIMUM_VALVE_MOVEMENT = 10
	MAXIMUM_TEST_TEMPERATURE = 100

	@staticmethod
	def require(condition, message):
		if not condition:
			raise CheckFailed(message)

	@staticmethod
	def is_temperature(value):
		return isinstance(value, (int, float)) and math.isfinite(value) and -100 < value < 200

	def wait_until(self, predicate, timeout):
		deadline = time.monotonic() + timeout
		while time.monotonic() < deadline:
			if predicate():
				return True
			if not self.wait(self.POLL_INTERVAL):
				return False
		return False

	@contextmanager
	def conditions(self, sensors=(), settings=()):
		"""Snapshot everything before writing; restore even on failure/cancellation."""
		saved_sensors, saved_settings = [], []
		self._status = 'FAIL'
		try:
			for sensor in sensors:
				self.require(sensor.is_mapped(), 'Не назначен необходимый датчик ИТП')
				state = 'short' if sensor.isShort() else 'open' if sensor.isOpen() else sensor.get_value()
				self.require(state is not None, 'Не прочитано исходное состояние датчика')
				saved_sensors.append((sensor, state, sensor.isManual()))
			for program, name, value in settings:
				original = program.read_parameter_value(name)
				self.require(original is not None, f'Не прочитан параметр {name}')
				saved_settings.append((program, name, original))
		except CheckFailed as error:
			print_error(str(error))
			yield False
			return
		prepared = True
		try:
			for program, name, value in settings:
				self.require(program.write_parameter(name, value), f'Не записан параметр {name}')
		except Exception as error:
			prepared = False
			print_error(str(error))
		try:
			yield prepared
		except CheckFailed as error:
			print_error(str(error))
			self._status = 'FAIL'
		finally:
			for sensor, state, manual in saved_sensors:
				try:
					try:
						self.set_sensor_value(sensor, state)
					finally:
						sensor.set_manual(manual)
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен датчик: {error}')
			for program, name, original in reversed(saved_settings):
				try:
					self.require(program.write_parameter(name, original), f'Не восстановлен параметр {name}')
				except Exception as error:
					self._status = 'FAIL'
					print_error(str(error))

	def set_sensor_value(self, sensor, value):
		# conditions() owns cleanup; Parent.clear() must not undo saved manual modes.
		sensor.set_manual(True)
		sensor.set_value(value, True)
		outdoor = getattr(self, '_virtual_outdoor', None)
		if outdoor is not None and sensor is outdoor.getOutdoorTemperature():
			outdoor.publish_temperature(force=True)

	def temperature_sensors(self):
		return tuple(self._district_heating.get_input_channel(name) for name in (
			'supply_direct_temp', 'supply_backward_temp', 'direct_temp', 'backward_temp'))

	def valve_settings(self):
		return (
			(self._district_heating, 'backwardControlType', self.BACKWARD_CONTROL_TYPE_CONST),
			(self._district_heating, 'valveRunningTime', self.VALVE_RUNNING_TIME),
		)

	def prepare_open_valve(self):
		for sensor, value in zip(self.temperature_sensors(), (
			self.CITY_SUPPLY, self.NORMAL_CITY_RETURN, self.COLD_HOUSE_SUPPLY, self.NORMAL_HOUSE_RETURN)):
			self.set_sensor_value(sensor, value)
		valve = self._district_heating.get_output_channel('analog_valve')
		self.require(valve.is_mapped(), 'Не назначен аналоговый клапан')
		print_log('Готовим открытый клапан при нормальном городском источнике')
		self.require(self.wait_until(lambda: valve.get_value() is not None
			and valve.get_value() >= self.OPEN_VALVE_SIGNAL, self.STARTUP_TIMEOUT),
			'Не удалось подготовить открытый клапан')
		return valve

	def run_valve_check(self, kind):
		with self.conditions(self.temperature_sensors(), self.valve_settings()) as ready:
			if not ready:
				return
			maximum = self.read_maximum_backward_temperature()
			self.require(self.is_temperature(maximum), 'Не прочитан настроенный предел обратки')
			self.require(self.wait_until(lambda: self.read_current_maximum_backward_temperature() == maximum,
				self.LIMIT_TIMEOUT), 'ИТП не пересчитал постоянный предел обратки')
			valve = self.prepare_open_valve()
			initial = valve.get_value()
			city_supply, city_return, house_supply, house_return = self.temperature_sensors()
			if kind == 'reversed_city_flow':
				# High house return bypasses the *other* return-limit protection.
				self.set_sensor_value(house_return, maximum + self.TEMPERATURE_MARGIN)
				self.set_sensor_value(city_return, self.CITY_SUPPLY + self.TEMPERATURE_MARGIN)
				delay, observation = self.REVERSED_FLOW_DELAY, self.VALVE_RUNNING_TIME
			else:
				test_return = maximum + self.TEMPERATURE_MARGIN
				self.require(test_return + self.TEMPERATURE_MARGIN <= self.MAXIMUM_TEST_TEMPERATURE,
					'Предел обратки слишком высок для изолированной проверки')
				self.set_sensor_value(city_supply, max(self.CITY_SUPPLY,
					test_return + self.TEMPERATURE_MARGIN))
				self.set_sensor_value(house_return, test_return if kind == 'high_house_return'
					else maximum - self.TEMPERATURE_MARGIN)
				self.set_sensor_value(city_return, test_return)
				delay, observation = self.RETURN_LIMIT_DELAY, self.VALVE_RUNNING_TIME * self.SLOW_CLOSING_FACTOR
			print_log(f'Предел {maximum} C; проверка {kind}, выдержка {delay} с')
			self.require(self.wait(delay), 'Проверка прервана')
			if kind == 'high_house_return':
				self.require(self.wait_state_permanence(lambda: valve.get_value() is not None
					and initial - valve.get_value() < self.MINIMUM_VALVE_MOVEMENT, observation),
					'Клапан закрылся при высокотемпературном потребителе')
			else:
				self.require(self.wait(observation), 'Проверка прервана')
				final = valve.get_value()
				self.require(final is not None and initial - final >= self.MINIMUM_VALVE_MOVEMENT, 'Клапан не начал закрываться')
			self._status = 'OK'

	def read_pressure_alarm(self, alarm):
		# The controller exposes this logical output even without physical mapping.
		return alarm.read_output(alarm.get_output_channel('alarm_output'))

	@contextmanager
	def pressure_alarm_conditions(self, alarm, pressure, settings):
		with self.conditions(self.temperature_sensors() + (pressure,), settings) as ready:
			try:
				yield ready
			finally:
				if ready:
					try:
						self.set_sensor_value(pressure, 'short')
						# pressureLossAlarmStatusGate resets the latch on a zero write.
						self.require(alarm.write_parameter('pressureLossAlarmReset', 0),
							'Не сброшена аварийная защёлка подпитки')
						self.require(self.wait_until(lambda: self.read_pressure_alarm(alarm) == self.RELAY_OFF,
							self.ALARM_STATUS_TIMEOUT), 'Не подтверждено снятие аварии при очистке')
					except Exception as error:
						self._status = 'FAIL'
						print_error(str(error))

	def run_pressure_alarm_check(self, reserve=False):
		alarm = self._programList['alarm']
		pressure = alarm.getPressure()
		settings = self.valve_settings() + (
			(self._district_heating, 'temperatureSourcePowerRequestDelay', self.ALARM_TEST_ON_DELAY),
			(alarm, 'pressureInputType', PRESSURE_INPUT_TYPE_OPENABLE),
			(alarm, 'autoFill', 0),
			(alarm, 'fillingDuration', self.ALARM_FILLING_DURATION),
		)
		if reserve:
			settings += ((self._programList['boiler'], 'minimumTemperatureRestriction', 0),)
		with self.pressure_alarm_conditions(alarm, pressure, settings) as ready:
			if not ready:
				return
			self.set_sensor_value(pressure, 'short')
			self.require(self.wait_until(lambda: self.read_pressure_alarm(alarm) == self.RELAY_OFF,
				self.ALARM_STATUS_TIMEOUT), 'Не подтверждено отсутствие аварии подпитки')
			self.prepare_open_valve()
			if reserve:
				boiler = self._programList['boiler']
				self.require(self.wait_backup_generator_not_requested(boiler,
					self.STARTUP_STABILIZATION_DURATION, self.STARTUP_TIMEOUT),
					'Резерв уже запрошен до аварии')
			else:
				loading = self._district_heating.get_output_channel('supply_pump')
				pump = self._district_heating.get_output_channel('circulation_pump')
				valve = self._district_heating.get_output_channel('analog_valve')
				self.require(loading.is_mapped() and pump.is_mapped(), 'Не назначены насосы ИТП')
				self.require(self.wait_until(lambda: loading.get_value() == self.RELAY_ON
					and pump.get_value() == self.RELAY_ON, self.STARTUP_TIMEOUT), 'Насосы не включились')
			print_log('Создаём обрыв: OPENABLE, подтверждаем аварию подпитки')
			self.set_sensor_value(pressure, 'open')
			self.require(self.wait_until(lambda: self.read_pressure_alarm(alarm) == self.RELAY_ON,
				self.ALARM_STATUS_TIMEOUT), 'Подпитка не подтвердила аварийное состояние')
			if reserve:
				self.require(self.wait_backup_generator_requested(boiler,
					self.ALARM_RESPONSE_STABILIZATION_DURATION, self.ALARM_RESPONSE_TIMEOUT),
					'ИТП не запросил резерв после подтверждённой аварии подпитки')
			else:
				self.require(self.wait_state_permanence(lambda: loading.get_value() == self.RELAY_OFF
					and pump.get_value() == self.RELAY_OFF and valve.get_value() == self.RELAY_OFF,
					self.ALARM_RESPONSE_STABILIZATION_DURATION, self.ALARM_RESPONSE_TIMEOUT),
					'ИТП не выключил насосы и клапан при подтверждённой аварии')
			self.set_sensor_value(pressure, 'short')
			self.require(self.wait_until(lambda: self.read_pressure_alarm(alarm) == self.RELAY_OFF,
				self.ALARM_STATUS_TIMEOUT), 'Авария подпитки не снялась')
			self._status = 'OK'
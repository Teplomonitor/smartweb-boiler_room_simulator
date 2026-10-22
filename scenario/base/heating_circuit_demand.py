import math
import time

from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter


class DemandCheckFailed(Exception):
	pass


class HeatingCircuitDemandScenario(Parent):
	TEST_ROOM = True
	HEATING_SLOPE = 0.8
	ROOM_SETPOINT = 20
	MINIMUM_FLOW = 15
	MAXIMUM_FLOW = 85
	ROOM_SHIFT_LIMIT = 15
	INTEGRAL_GAIN = 30
	# CircuitProgram recalculates every 10 s; allow two cycles for reset.
	RESET_DURATION = 20
	INPUT_TIMEOUT = 6 * 60
	DEMAND_TIMEOUT = 90
	STABLE_DURATION = 20
	INTEGRAL_DURATION = 2 * 60
	MINIMUM_INTEGRAL_CHANGE = 1.4
	INPUT_TOLERANCE = 0.2
	DEMAND_TOLERANCE = 0.6
	POLL_INTERVAL = 2
	LOG_INTERVAL = 10
	PUMP_MODE_ALWAYS_ON = 2
	ROOM_MODE_COMFORT = 0  # schedule::MODE_COMFORT

	def force_preset_load(self):
		# Fresh programs also select the standard (not manual) weather curve.
		return True

	def get_default_preset(self):
		return 'heating_circuit_3_3_5'

	def get_required_programs(self):
		return {
			'heating_circuit': snc.ProgramType.HEATING_CIRCUIT,
			'outdoor': snc.ProgramType.OUTDOOR_SENSOR,
			'room': snc.ProgramType.ROOM_DEVICE,
			'boiler': snc.ProgramType.BOILER,
		}

	def _read_parameter(self, program, program_type, parameter_id):
		parameter = RemoteControlParameter(
			programType=program_type, parameterId=parameter_id, programId=program.get_id(),
		)
		return parameter.get_value() if parameter.read() else None

	def _write_parameter(self, program, program_type, parameter_id, value):
		return RemoteControlParameter(
			programType=program_type, parameterId=parameter_id,
			programId=program.get_id(), parameterValue=value,
		).write()

	def _put(self, program, program_type, parameter_id, value):
		if not self._write_parameter(program, program_type, parameter_id, value):
			raise DemandCheckFailed(f'Не записан параметр {program_type}/{parameter_id}: {value}')

	def _set_circuit(self, parameter_id, value):
		self._put(self._circuit, snc.ProgramType.CIRCUIT, parameter_id, value)

	def _settings(self):
		circuit = snc.CircuitParameterId
		room = snc.RoomDeviceParameterId
		shift = self.ROOM_SHIFT_LIMIT if self.TEST_ROOM else 0
		return [
			(self._circuit, snc.ProgramType.CIRCUIT, circuit.HEAT_CALCULATION_MODE,
			 snc.ConsumerHeatCalculationMode.WEATHER_HEATING_SLOPE),
			(self._circuit, snc.ProgramType.CIRCUIT, circuit.HEATING_SLOPE, self.HEATING_SLOPE),
			(self._circuit, snc.ProgramType.CIRCUIT, circuit.MINIMUM_FLOW_TEMPERATURE, self.MINIMUM_FLOW),
			(self._circuit, snc.ProgramType.CIRCUIT, circuit.MAXIMUM_FLOW_TEMPERATURE, self.MAXIMUM_FLOW),
			(self._circuit, snc.ProgramType.CIRCUIT, circuit.ROOM_SENSOR_INFLUENCE, 0),
			# Influence=0 only resets integration; these bounds disable the P term too.
			(self._circuit, snc.ProgramType.CIRCUIT, circuit.ROOM_SENSOR_INFLUENCE_MIN, -shift),
			(self._circuit, snc.ProgramType.CIRCUIT, circuit.ROOM_SENSOR_INFLUENCE_MAX, shift),
			(self._circuit, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.TEMPERATURE_COMPENSATION, 0),
			(self._circuit, snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.PUMP_MODE,
			 self.PUMP_MODE_ALWAYS_ON),
			(self._room, snc.ProgramType.ROOM_DEVICE, room.WORK_MODE, self.ROOM_MODE_COMFORT),
			(self._room, snc.ProgramType.ROOM_DEVICE, room.ROOM_COMFORT_TEMPERATURE, self.ROOM_SETPOINT),
			(self._room, snc.ProgramType.ROOM_DEVICE, room.RESPONSIBLE_CIRCUIT_1, self._circuit.get_id()),
			(self._room, snc.ProgramType.ROOM_DEVICE, room.RESPONSIBLE_CIRCUIT_2, 0),
			(self._room, snc.ProgramType.ROOM_DEVICE, room.RESPONSIBLE_CIRCUIT_3, 0),
			(self._room, snc.ProgramType.ROOM_DEVICE, room.CIRCUIT_1_SHIFT, 0),
		]

	@staticmethod
	def _is_number(value):
		return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

	def _close(self, value, expected, tolerance):
		return self._is_number(value) and abs(value - expected) <= tolerance

	def _inputs_match(self, outdoor, room, setpoint):
		parameter = snc.CircuitParameterId
		for parameter_id, expected in (
			(parameter.OUTDOOR_TEMPERATURE, outdoor),
			(parameter.CURRENT_SUPPORTED_ROOM_DEVICE_TEMPERATURE, room),
			(parameter.CURRENT_SUPPORTED_ROOM_DEVICE_REQUIRED_TEMPERATURE, setpoint),
		):
			value = self._read_parameter(self._circuit, snc.ProgramType.CIRCUIT, parameter_id)
			if not self._close(value, expected, self.INPUT_TOLERANCE):
				return False
		return self._read_parameter(
			self._circuit, snc.ProgramType.CIRCUIT, parameter.CURRENT_SUPPORTED_ROOM_DEVICE_ID,
		) == self._room.get_id()

	def _demand(self):
		return self._read_parameter(
			self._circuit, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
		)

	def _require(self, condition, message):
		if not condition:
			raise DemandCheckFailed(message)

	def _check_point(self, outdoor, room, setpoint, expected, reset_integral=True):
		print_log(f'Улица={outdoor:+g} C; помещение={room:g} C; уставка={setpoint:g} C; запрос={expected:g} C')
		if reset_integral:
			self._set_circuit(snc.CircuitParameterId.ROOM_SENSOR_INFLUENCE, 0)
			self._require(self.wait(self.RESET_DURATION), 'Прерван сброс интегральной поправки')
		self._outdoor_sensor.set_value(outdoor, True)
		self._room_sensor.set_value(room, True)
		self._put(self._room, snc.ProgramType.ROOM_DEVICE,
			snc.RoomDeviceParameterId.ROOM_COMFORT_TEMPERATURE, setpoint)
		self._require(self.wait_event(
			lambda: self._inputs_match(outdoor, room, setpoint), self.INPUT_TIMEOUT,
		), 'Контур не принял уличную/комнатную температуру, уставку или ID помещения')
		last_demand = None

		def matches():
			nonlocal last_demand
			last_demand = self._demand()
			return self._inputs_match(outdoor, room, setpoint) and self._close(
				last_demand, expected, self.DEMAND_TOLERANCE,
			)

		self._require(self.wait_state_permanence(matches, self.STABLE_DURATION, self.DEMAND_TIMEOUT),
			f'Неверный запрос: ожидалось {expected:g} C, получено {last_demand}')
		return last_demand

	def _check_integral(self, outdoor, room, expected):
		baseline = self._check_point(outdoor, room, self.ROOM_SETPOINT, expected)
		self._set_circuit(snc.CircuitParameterId.ROOM_SENSOR_INFLUENCE, self.INTEGRAL_GAIN)
		direction = 1 if room < self.ROOM_SETPOINT else -1
		deadline = time.monotonic() + self.INTEGRAL_DURATION
		next_log = 0
		last_demand = baseline
		while time.monotonic() < deadline:
			self._require(self.wait(self.POLL_INTERVAL), 'Прервана проверка интегральной поправки')
			self._require(self._inputs_match(outdoor, room, self.ROOM_SETPOINT),
				'Изменились входы контура при проверке интегральной поправки')
			demand = self._demand()
			self._require(self._is_number(demand), f'Не прочитан запрос контура: {demand}')
			self._require(self.MINIMUM_FLOW <= demand <= self.MAXIMUM_FLOW,
				f'Запрос вне допустимых границ: {demand}')
			self._require(direction * (demand - last_demand) >= -self.DEMAND_TOLERANCE,
				'Комнатная коррекция изменяется в неверную сторону')
			last_demand = demand
			if time.monotonic() >= next_log:
				print_log(f'Интегральная коррекция: начальный запрос={baseline:g} C, текущий={demand:g} C')
				next_log = time.monotonic() + self.LOG_INTERVAL
		self._require(direction * (last_demand - baseline) >= self.MINIMUM_INTEGRAL_CHANGE,
			'При постоянной комнатной ошибке запрос не продолжил изменяться')
		return last_demand

	def _run_test(self, sequence):
		self._status = 'FAIL'
		self._circuit = self._programList['heating_circuit']
		self._room = self._programList['room']
		self._outdoor_sensor = self._programList['outdoor'].get_input_channel('outdoorTemperature')
		self._room_sensor = self._room.get_input_channel('roomTemperature')
		sensors = (self._outdoor_sensor, self._room_sensor)
		saved_sensors = []
		for sensor in sensors:
			value = sensor.get_value()
			if not sensor.is_mapped() or not self._is_number(value) or sensor.isShort() or sensor.isOpen():
				print_error('Требуются исправные и назначенные уличный и комнатный датчики')
				return
			saved_sensors.append((sensor, value, sensor.isManual()))
		settings = self._settings()
		saved = []
		for program, program_type, parameter_id, _ in settings:
			value = self._read_parameter(program, program_type, parameter_id)
			if value is None:
				print_error(f'Не прочитан исходный параметр {program_type}/{parameter_id}')
				return
			saved.append((program, program_type, parameter_id, value))
		try:
			for sensor in sensors:
				# Avoid _manualSensorsList: clear() must not undo restored manual modes.
				sensor.set_manual(True)
			for setting in settings:
				self._put(*setting)
			sequence()
			self._status = 'OK'
		except DemandCheckFailed as error:
			print_error(str(error))
		finally:
			for program, program_type, parameter_id, value in reversed(saved):
				try:
					self._put(program, program_type, parameter_id, value)
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен параметр {program_type}/{parameter_id}: {error}')
			for sensor, value, manual in saved_sensors:
				try:
					try:
						sensor.set_value(value, True)
					finally:
						sensor.set_manual(manual)
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен датчик: {error}')
import math
import time

from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter


class HeatingCircuitMixerScenario(Parent):
	HOT_BOILER_TEMPERATURE = 70
	COLD_BOILER_TEMPERATURE = 35
	LOW_SETPOINT = 40
	HIGH_SETPOINT = 50
	TEMPERATURE_TOLERANCE = 2
	SOURCE_TOLERANCE = 3
	SOURCE_HEADROOM = 10
	COLD_DEFICIT = 5
	# Both actuator types report position on the analog relay scale (0..254).
	VALVE_MOVEMENT = 5
	VALVE_SATURATED = 249
	PUMP_MODE_ALWAYS_ON = 2  # HeatingCircuitProgram::PUMP_MODE_ALWAYS_ON
	VALVE_RUNNING_TIME = 120  # RemoteControl TIME_MS values are expressed in seconds.
	VALVE_PROPORTIONAL_BAND = 10
	STABILIZATION_DURATION = 30
	REGULATION_TIMEOUT = 8 * 60
	SETPOINT_TIMEOUT = 60
	POLL_INTERVAL = 1
	LOG_INTERVAL = 10

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'heating_circuit': snc.ProgramType.HEATING_CIRCUIT,
			'boiler': snc.ProgramType.BOILER,
		}

	def get_scenario_description(self):
		return (
			'Смеситель поддерживает температуру при изменении уставки; '
			'при холодном котле открывается полностью, после прогрева восстанавливает регулирование. '
			'Температура котла задаётся вручную, контур работает в штатной симуляции.'
		)

	def _read_parameter(self, program, program_type, parameter_id):
		parameter = RemoteControlParameter(
			programType=program_type, parameterId=parameter_id, programId=program.get_id(),
		)
		return parameter.get_value() if parameter.read() else None

	def _write_parameter(self, program, program_type, parameter_id, value):
		parameter = RemoteControlParameter(
			programType=program_type, parameterId=parameter_id,
			programId=program.get_id(), parameterValue=value,
		)
		return parameter.write()

	def _settings(self):
		circuit = snc.ProgramType.CIRCUIT
		heating = snc.ProgramType.HEATING_CIRCUIT
		boiler = snc.ProgramType.BOILER
		generator = snc.ProgramType.TEMPERATURE_GENERATOR
		return [
			(self._circuit, circuit, snc.CircuitParameterId.HEAT_CALCULATION_MODE,
			 snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE),
			(self._circuit, circuit, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, self.LOW_SETPOINT),
			(self._circuit, circuit, snc.CircuitParameterId.MINIMUM_FLOW_TEMPERATURE, 15),
			(self._circuit, circuit, snc.CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE, 85),
			(self._circuit, heating, snc.HeatingCircuitParameterId.PUMP_MODE, self.PUMP_MODE_ALWAYS_ON),
			(self._circuit, heating, snc.HeatingCircuitParameterId.VALVE_RUNING_TIME, self.VALVE_RUNNING_TIME),
			(self._circuit, heating, snc.HeatingCircuitParameterId.VALVE_OPEN_PROPORTIONAL_BAND, self.VALVE_PROPORTIONAL_BAND),
			(self._circuit, heating, snc.HeatingCircuitParameterId.VALVE_CLOSE_PROPORTIONAL_BAND, self.VALVE_PROPORTIONAL_BAND),
			# A cold source must not restrict the mixer via boiler warm-up requests.
			(self._boiler, boiler, snc.BoilerParameterId.WARMUP_TEMPERATURE, 20),
			(self._boiler, boiler, snc.BoilerParameterId.BOILER_COOLING, 0),
			(self._boiler, generator, snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION, 0),
		]

	def _setpoint(self, value):
		if not self._write_parameter(
			self._circuit, snc.ProgramType.CIRCUIT,
			snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, value,
		):
			print_error(f'Не удалось записать уставку {value} C')
			return False
		# Verify the actual controller demand, not just a successful write.
		if not self.wait_event(
			lambda: self._read_parameter(
				self._circuit, snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
			) == value,
			self.SETPOINT_TIMEOUT,
		):
			print_error(f'Контроллер не принял требуемую температуру {value} C')
			return False
		return True

	def _get_valve_channels(self):
		self._valve = self._circuit.get_output_channel('analogValve')
		return (self._valve,)

	def _valve_mappings_valid(self):
		return True

	def _valve_position(self):
		return self._valve.get_value()

	def _sample_is_safe(self, sample):
		return True

	def _sample(self):
		return {
			'boiler': self._boiler_sensor.get_value(),
			'source': self._model.getSourceTemperature(),
			'flow': self._flow_sensor.get_value(),
			'valve': self._valve_position(),
			'pump': self._pump.get_value(),
		}

	def _matches(self, sample, setpoint, cold, baseline, direction):
		if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in sample.values()):
			return False
		if not 0 <= sample['valve'] <= self.RELAY_MAX or sample['pump'] != self.RELAY_ON:
			return False
		if abs(sample['source'] - sample['boiler']) > self.SOURCE_TOLERANCE:
			return False
		if baseline is not None and direction * (sample['valve'] - baseline) < self.VALVE_MOVEMENT:
			return False
		if cold:
			return (
				sample['source'] <= setpoint - self.COLD_DEFICIT
				and sample['flow'] <= setpoint - self.COLD_DEFICIT
				and abs(sample['flow'] - sample['source']) <= self.TEMPERATURE_TOLERANCE
				and sample['valve'] >= self.VALVE_SATURATED
			)
		return (
			sample['source'] >= setpoint + self.SOURCE_HEADROOM
			and abs(sample['flow'] - setpoint) <= self.TEMPERATURE_TOLERANCE
			and self.RELAY_MIN < sample['valve'] < self.VALVE_SATURATED
		)

	def _check_phase(self, title, setpoint, cold=False, baseline=None, direction=0):
		print_log(title)
		deadline = time.monotonic() + self.REGULATION_TIMEOUT
		stable_since = None
		next_log = 0
		while time.monotonic() < deadline:
			if not self.wait(self.POLL_INTERVAL):
				return None
			sample = self._sample()
			if not self._sample_is_safe(sample):
				return None
			now = time.monotonic()
			if now >= next_log:
				print_log(f'Уставка={setpoint} C; {sample}')
				next_log = now + self.LOG_INTERVAL
			if self._matches(sample, setpoint, cold, baseline, direction):
				if stable_since is None:
					stable_since = now
				if now - stable_since >= self.STABILIZATION_DURATION:
					return sample['valve']
			else:
				stable_since = None
		print_error(f'{title}: состояние не стабилизировалось за {self.REGULATION_TIMEOUT} с')
		return None

	def _run_test(self):
		self._status = 'FAIL'
		self._circuit = self._programList['heating_circuit']
		self._boiler = self._programList['boiler']
		self._boiler_sensor = self._boiler.get_input_channel('temperature')
		self._flow_sensor = self._circuit.get_input_channel('temperature')
		valve_channels = self._get_valve_channels()
		self._pump = self._circuit.get_output_channel('pump')
		if not all(channel.is_mapped() for channel in (
			self._boiler_sensor, self._flow_sensor, self._pump, *valve_channels,
		)) or not self._valve_mappings_valid():
			print_error('Отсутствуют обязательные датчики или выходы контура/котла либо неверен тип смесителя')
			return
		if self._flow_sensor.isManual():
			print_error('Датчик контура должен работать в автоматическом режиме симуляции')
			return
		self._model = next((
			model for model in self._sim.getHeatingCircuitList()
			if model._program is self._circuit
		), None)
		if self._model is None:
			print_error('Не найдена тепловая модель отопительного контура')
			return

		settings = self._settings()
		saved = []
		for program, program_type, parameter_id, _ in settings:
			value = self._read_parameter(program, program_type, parameter_id)
			if value is None:
				print_error(f'Не удалось прочитать исходный параметр {program_type}/{parameter_id}')
				return
			saved.append((program, program_type, parameter_id, value))
		sensor_value = self._boiler_sensor.get_value()
		sensor_manual = self._boiler_sensor.isManual()
		if sensor_value is None or self._boiler_sensor.isShort() or self._boiler_sensor.isOpen():
			print_error('Исходный датчик котла должен иметь нормальную температуру')
			return
		try:
			for program, program_type, parameter_id, value in settings:
				if not self._write_parameter(program, program_type, parameter_id, value):
					print_error(f'Не удалось записать параметр {program_type}/{parameter_id}')
					return
			# Do not register with set_sensor_value(): clear() would discard a
			# pre-existing manual mode after this finally block restored it.
			self._boiler_sensor.set_manual(True)
			self._boiler_sensor.set_value(self.HOT_BOILER_TEMPERATURE, True)
			last_valve = None
			for setpoint, direction in ((self.LOW_SETPOINT, 0), (self.HIGH_SETPOINT, 1), (self.LOW_SETPOINT, -1)):
				if not self._setpoint(setpoint):
					return
				last_valve = self._check_phase(
					f'Горячий котёл: поддержание {setpoint} C', setpoint,
					baseline=last_valve, direction=direction,
				)
				if last_valve is None:
					return
			self._boiler_sensor.set_value(self.COLD_BOILER_TEMPERATURE, True)
			last_valve = self._check_phase(
				'Холодный котёл: полное открытие без требования достичь уставки',
				self.LOW_SETPOINT, cold=True, baseline=last_valve, direction=1,
			)
			if last_valve is None:
				return
			self._boiler_sensor.set_value(self.HOT_BOILER_TEMPERATURE, True)
			if self._check_phase(
				'Прогрев котла: восстановление регулирования', self.LOW_SETPOINT,
				baseline=last_valve, direction=-1,
			) is None:
				return
			self._status = 'OK'
		finally:
			# Attempt every restoration even if a controller write fails.
			for program, program_type, parameter_id, value in reversed(saved):
				try:
					if not self._write_parameter(program, program_type, parameter_id, value):
						raise RuntimeError('нет подтверждения записи')
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен параметр {program_type}/{parameter_id}: {error}')
			try:
				self._boiler_sensor.set_value(sensor_value, True)
			finally:
				self._boiler_sensor.set_manual(sensor_manual)

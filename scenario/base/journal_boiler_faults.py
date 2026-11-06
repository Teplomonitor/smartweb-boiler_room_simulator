"""Black-box boiler journal checks; firmware timers are not accelerated."""

from contextlib import contextmanager
from math import isfinite
import time

from consoleLog import print_error, print_log
from scenario.base.cascade_manager import CascadeManagerScenario
from scenario.base.journal import JournalScenarioMixin
from scenario.scenario import ThreadStoppedException
from scenario.steps import preserved_inputs
import smartnet.constants as snc
from smartnet.message_log_constants import MessageLogCode as Code, SeverityCode as Severity


class JournalBoilerFaultScenario(JournalScenarioMixin, CascadeManagerScenario):
	LOW_POWER = True
	ALARM_DELAY = 50 * 60
	ESTIMATED_RUN_SECONDS = 3300
	BASELINE_HOLD = 35
	INPUT_TIMEOUT = 30
	START_TIMEOUT = 90
	EARLY_TOLERANCE = 5
	LATE_TOLERANCE = 120
	POLL_INTERVAL = 2
	SETPOINT = 70
	BASELINE_TEMPERATURE = 60
	BASELINE_RETURN = 20
	WARMUP_TEMPERATURE = 30
	HYSTERESIS = 5
	PUMP_ALWAYS_ON = 2
	clock = staticmethod(time.monotonic)

	def get_required_programs(self):
		return {'circuit': snc.ProgramType.HEATING_CIRCUIT, 'boiler': snc.ProgramType.BOILER}

	def get_default_preset(self):
		return 'journal_boiler_faults'

	def fault_temperatures(self):
		# 9.34 must exclude the higher-priority low-power condition.
		return (40, 40) if self.LOW_POWER else (20, 5)

	def expected_code(self):
		return Code.MLC_BOILER_POWER_IS_LOW if self.LOW_POWER else Code.MLC_BOILER_TEMPERATURE_IS_LOW

	def settings(self):
		p = self._programList
		settings = []
		for program in p.values():
			for key in (snc.ProgramParameterId.TRAINING_ENABLED, snc.ProgramParameterId.MANUAL_MODE_ENABLED):
				settings.append((program, snc.ProgramType.PROGRAM, key, 0))
		for kind, key, value in (
			(snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.PUMP_MODE, self.PUMP_ALWAYS_ON),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.HEAT_CALCULATION_MODE,
			 snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, self.SETPOINT),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MINIMUM_FLOW_TEMPERATURE, 0),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE, 90),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.ROOM_SENSOR_INFLUENCE, 0),
			(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.PRIORITY, 0),
			(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.TEMPERATURE_COMPENSATION, 0),
			(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.HEAT_EXTRICATION_ENABLED, 0),
		):
			settings.append((p['circuit'], kind, key, value))
		for key, value in (
			(snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION, 0),
			(snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE, 0),
			(snc.TemperatureGeneratorParameterId.MAXIMUM_TEMPERATURE, 90),
			(snc.TemperatureGeneratorParameterId.ABSOLUTE_HYSTERESIS, self.HYSTERESIS),
		):
			settings.append((p['boiler'], snc.ProgramType.TEMPERATURE_GENERATOR, key, value))
		settings.append((p['boiler'], snc.ProgramType.BOILER,
			snc.BoilerParameterId.WARMUP_TEMPERATURE, self.WARMUP_TEMPERATURE))
		return settings

	@contextmanager
	def fault_configuration(self):
		boiler = self._programList['boiler']
		circuit = self._programList['circuit']
		self._flow_sensor = boiler.get_input_channel('temperature')
		self._return_sensor = boiler.get_input_channel('backwardTemperature')
		sensors = [self._flow_sensor, self._return_sensor, circuit.get_input_channel('temperature')]
		for sensor in sensors:
			if sensor is None or not sensor.is_mapped():
				raise RuntimeError('Не назначен необходимый датчик')
			value = sensor.get_value()
			if not isinstance(value, (int, float)) or not isfinite(value):
				raise RuntimeError('Нет исходной температуры датчика')
		for program, name in ((boiler, 'burner1'), (circuit, 'pump')):
			channel = program.get_output_channel(name)
			if channel is None or not channel.is_mapped():
				raise RuntimeError(f'Не назначен выход {name}')
		settings = self.settings()
		saved = [(program, kind, key, self.read_parameter(program, kind, key))
			for program, kind, key, _ in settings]
		attempted = []
		with preserved_inputs(self, sensors):
			try:
				for sensor, value in zip(sensors,
						(self.BASELINE_TEMPERATURE, self.BASELINE_RETURN, self.SETPOINT)):
					self.set_sensor_value(sensor, value)
				for setting, original in zip(settings, saved):
					attempted.append(original)
					self.write_parameter(*setting)
				yield
			finally:
				errors = []
				for original in reversed(attempted):
					try:
						self.write_parameter(*original)
					except Exception as error:
						errors.append(str(error))
				if errors:
					raise RuntimeError('Не восстановлены параметры: ' + '; '.join(errors))

	def inputs_are(self, flow, backward):
		boiler = self._programList['boiler']
		return all(abs(self.read_parameter(boiler, snc.ProgramType.PROGRAM,
			snc.ProgramParameterId.INPUT, index=index) - expected) <= self.TEMPERATURE_TOLERANCE
			for index, expected in enumerate((flow, backward)))

	def operating_state_is_valid(self):
		boiler = self._programList['boiler']
		circuit = self._programList['circuit']
		for program, output in ((boiler, 'burner1'), (circuit, 'pump')):
			value = program.get_output_channel(output).get_value()
			if value is None or value == self.RELAY_OFF:
				return False
		required = self.read_parameter(boiler, snc.ProgramType.TEMPERATURE_SOURCE,
			snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE)
		return abs(required - self.SETPOINT) <= self.TEMPERATURE_TOLERANCE

	def checked_wait(self, duration):
		if self.wait(duration) is False:
			raise ThreadStoppedException('Проверка журнала котла прервана')

	def observe_fault(self, started, confirmed):
		fault_codes = {Code.MLC_BOILER_POWER_IS_LOW, Code.MLC_BOILER_TEMPERATURE_IS_LOW,
			Code.MLC_BOILER_ERROR, Code.MLC_PROGRAM_VERY_LOW_TEMPERATURE}
		while True:
			entries = self._read_journal(self._journal_cursor)
			if entries is None:
				raise RuntimeError('Не удалось полностью прочитать журнал')
			if entries:
				self._journal_cursor = entries[-1]
			matched = False
			for entry in entries:
				if entry.param != self._programList['boiler'].get_id() or entry.code not in fault_codes:
					continue
				if entry.code != self.expected_code() or entry.severity != Severity.SC_WARNING:
					raise RuntimeError('Неверный код или важность аварии котла')
				if not started + self.ALARM_DELAY - self.EARLY_TOLERANCE <= self.clock() <= confirmed + self.ALARM_DELAY + self.LATE_TOLERANCE:
					raise RuntimeError('Авария котла возникла вне допустимого временного окна')
				matched = True
			if not self.inputs_are(*self.fault_temperatures()):
				raise RuntimeError('Нарушена выдержка температур котла')
			if matched:
				# The fault itself may switch the burner off; do not reject that transition.
				return
			if not self.operating_state_is_valid():
				raise RuntimeError('Во время выдержки пропал запрос тепла или отключилась ступень котла')
			if self.clock() >= confirmed + self.ALARM_DELAY + self.LATE_TOLERANCE:
				raise RuntimeError('Нет новой записи об аварии котла за 50 минут с допуском')
			self.checked_wait(self.POLL_INTERVAL)

	def run_fault_test(self):
		self._status = 'FAIL'
		try:
			with self.fault_configuration():
				def ready():
					return (self.inputs_are(self.BASELINE_TEMPERATURE, self.BASELINE_RETURN)
						and self.operating_state_is_valid()
						and self.read_parameter(self._programList['boiler'], snc.ProgramType.TEMPERATURE_SOURCE,
							snc.TemperatureSourceParameterId.ERROR_STATE) == 0)
				if not self.wait_event(ready, self.START_TIMEOUT):
					raise RuntimeError('Котёл не вышел в исходное рабочее состояние без аварии')
				self.checked_wait(self.BASELINE_HOLD)
				if not ready() or not self.snapshot_journal():
					return
				flow, backward = self.fault_temperatures()
				self.set_sensor_value(self._return_sensor, backward)
				started = self.clock()
				self.set_sensor_value(self._flow_sensor, flow)
				if not self.wait_event(lambda: self.inputs_are(flow, backward), self.INPUT_TIMEOUT):
					raise RuntimeError('Контроллер не подтвердил тестовые температуры')
				confirmed = self.clock()
				print_log('Проверка аварии котла: выдержка 50 минут без ускорения таймера')
				self.observe_fault(started, confirmed)
			self._status = 'OK'
		except ThreadStoppedException:
			raise
		except Exception as error:
			print_error(str(error))
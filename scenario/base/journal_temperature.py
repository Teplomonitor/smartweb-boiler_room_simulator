"""Black-box journal checks; firmware timers run in real time, without acceleration."""

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import time

from consoleLog import print_error, print_log
from scenario.base.cascade_manager import CascadeManagerScenario
from scenario.base.journal import JournalScenarioMixin
from scenario.scenario import ThreadStoppedException
from scenario.steps import preserved_inputs
import smartnet.constants as snc
from smartnet.message_log_constants import MessageLogCode as Code, SeverityCode as Severity


@dataclass
class TemperatureCheck:
	name: str
	program: object
	sensor: object
	cold: float
	warm: float
	delay: int
	code: int
	severity: int
	recovery_code: int = None
	recovery_severity: int = Severity.SC_NOTICE
	recovery_delay: int = 0
	intermediate: float = None
	phase: str = 'cold'
	changed_at: float = 0
	confirmed_at: float = 0
	cold_ok: bool = False
	recovery_ok: bool = False
	invalid: bool = False
	recovery_invalid: bool = False


class JournalTemperatureScenario(JournalScenarioMixin, CascadeManagerScenario):
	SEVERE = False
	PUMP_ALWAYS_ON = 2
	CIRCUIT_MINIMUM = 30
	CIRCUIT_SETPOINT = 50
	DHW_SETPOINT = 55
	DHW_HYSTERESIS = 5
	CASCADE_MINIMUM = 45
	CASCADE_SETPOINT = 60
	BOILER_MINIMUM = 50
	BOILER_WARMUP = 30
	SOURCE_TEMPERATURE = 65
	ROOM_OFF_TEMPERATURE = 10
	HALF_HOUR = 30 * 60
	ONE_HOUR = 60 * 60
	RECOVERY_DELAY = 30
	GENERATOR_ALARM_STAGGER = 30
	INTERMEDIATE_HOLD = 45
	BASELINE_HOLD = 35
	INPUT_TIMEOUT = 30
	EARLY_TOLERANCE = 5
	LATE_TOLERANCE = 120
	RECOVERY_TIMEOUT = 60
	OBSERVATION_INTERVAL = 10
	POLL_INTERVAL = 2
	clock = staticmethod(time.monotonic)

	def get_required_programs(self):
		programs = {'circuit': snc.ProgramType.HEATING_CIRCUIT, 'boiler': snc.ProgramType.BOILER}
		if self.SEVERE:
			programs.update(cascade=snc.ProgramType.CASCADE_MANAGER, room=snc.ProgramType.ROOM_DEVICE)
		else:
			programs['dhw'] = snc.ProgramType.DHW
		return programs

	def get_checklist_results(self):
		ids = ('9.18', '9.19') if self.SEVERE else ('9.16', '9.17')
		return dict(getattr(self, '_checklist_results', dict.fromkeys(ids, 'FAIL')))

	def settings(self):
		p = self._programList
		settings = []
		for program in p.values():
			settings.extend([
				(program, snc.ProgramType.PROGRAM, snc.ProgramParameterId.TRAINING_ENABLED, 0),
				(program, snc.ProgramType.PROGRAM, snc.ProgramParameterId.MANUAL_MODE_ENABLED, 0),
			])
		circuit = p['circuit']
		setpoint = self.CASCADE_SETPOINT if self.SEVERE else self.CIRCUIT_SETPOINT
		for program_type, parameter_id, value in (
			(snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.PUMP_MODE, self.PUMP_ALWAYS_ON),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.HEAT_CALCULATION_MODE,
			 snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, setpoint),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MINIMUM_FLOW_TEMPERATURE, self.CIRCUIT_MINIMUM),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE, 90),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.ROOM_SENSOR_INFLUENCE, 0),
		):
			settings.append((circuit, program_type, parameter_id, value))
		consumers = [circuit] if self.SEVERE else [circuit, p['dhw']]
		for consumer in consumers:
			for parameter_id in (snc.ConsumerParameterId.PRIORITY,
					snc.ConsumerParameterId.TEMPERATURE_COMPENSATION,
					snc.ConsumerParameterId.HEAT_EXTRICATION_ENABLED):
				settings.append((consumer, snc.ProgramType.CONSUMER, parameter_id, 0))
		generator = snc.TemperatureGeneratorParameterId
		for parameter_id, value in (
			(generator.MINIMUM_TEMPERATURE_RESTRICTION, int(self.SEVERE)),
			(generator.MINIMUM_TEMPERATURE, self.BOILER_MINIMUM if self.SEVERE else 0),
			(generator.MAXIMUM_TEMPERATURE, 90),
			(generator.ABSOLUTE_HYSTERESIS, 5),
		):
			settings.append((p['boiler'], snc.ProgramType.TEMPERATURE_GENERATOR, parameter_id, value))
		settings.append((p['boiler'], snc.ProgramType.BOILER,
			snc.BoilerParameterId.WARMUP_TEMPERATURE, self.BOILER_WARMUP))
		if self.SEVERE:
			for parameter_id, value in (
				(snc.CascadeManagerParameterId.MINIMUM_REQUIRED_TEMPERATURE, self.CASCADE_MINIMUM),
				(snc.CascadeManagerParameterId.MAXIMUM_REQUIRED_TEMPERATURE, 90),
				(snc.CascadeManagerParameterId.TEMPERATURE_OFFSET, 0),
				(snc.CascadeManagerParameterId.PARAM_P_FACTOR, 20),
				(snc.CascadeManagerParameterId.PARAM_I_FACTOR, 0),
				(snc.CascadeManagerParameterId.PARAM_D_FACTOR, 0),
				(snc.CascadeManagerParameterId.WORK_FUNCTION, 0),
				(snc.CascadeManagerParameterId.ROTATION_TYPE, 0),
				(snc.CascadeManagerParameterId.NEXT_TEMPERATURE_SRC_ON_DELAY, 0),
			):
				settings.append((p['cascade'], snc.ProgramType.CASCADE_MANAGER, parameter_id, value))
			settings.append((p['room'], snc.ProgramType.ROOM_DEVICE,
				snc.RoomDeviceParameterId.ROOM_OFF_TEMPERATURE, self.ROOM_OFF_TEMPERATURE))
		else:
			for parameter_id, value in (
				(snc.DhwParameterId.WORK_MODE, 0),
				(snc.DhwParameterId.TEMPERATURE_COMFORT, self.DHW_SETPOINT),
				(snc.DhwParameterId.TEMPERATURE_HYSTERESIS, self.DHW_HYSTERESIS),
				(snc.DhwParameterId.ANTILEGION, 0),
				(snc.DhwParameterId.DHW_RELIEF, 0),
			):
				settings.append((p['dhw'], snc.ProgramType.DHW, parameter_id, value))
		return settings

	def make_checks(self):
		p = self._programList
		def check(name, channel, cold, warm, delay, code, severity, **kwargs):
			program = p[name]
			return TemperatureCheck(name, program, program.get_input_channel(channel),
				cold, warm, delay, code, severity, **kwargs)

		if not self.SEVERE:
			return [
				check('circuit', 'temperature', 40, self.CIRCUIT_SETPOINT, self.HALF_HOUR,
					Code.MLC_CONSUMER_UNDERHEATING_START, Severity.SC_NOTICE,
					recovery_code=Code.MLC_CONSUMER_UNDERHEATING_OVER),
				check('dhw', 'temperature', 45, self.DHW_SETPOINT, self.ONE_HOUR,
					Code.MLC_CONSUMER_UNDERHEATING_START, Severity.SC_NOTICE,
					recovery_code=Code.MLC_CONSUMER_UNDERHEATING_OVER),
			]
		return [
			check('cascade', 'temperature', 35, self.CASCADE_SETPOINT, self.ONE_HOUR,
				Code.MLC_PROGRAM_VERY_LOW_TEMPERATURE, Severity.SC_WARNING,
				recovery_code=Code.MLC_LOW_TEMPERATURE_STOP,
				recovery_severity=Severity.SC_INFORMATIONAL,
				recovery_delay=self.RECOVERY_DELAY, intermediate=50),
			check('circuit', 'temperature', 20, self.CASCADE_SETPOINT, self.HALF_HOUR,
				Code.MLC_PROGRAM_VERY_LOW_TEMPERATURE, Severity.SC_WARNING),
			check('room', 'roomTemperature', 5, 20, self.HALF_HOUR,
				Code.MLC_PROGRAM_VERY_LOW_TEMPERATURE, Severity.SC_ERROR),
			check('boiler', 'temperature', 40, self.SOURCE_TEMPERATURE, self.ONE_HOUR,
				Code.MLC_PROGRAM_VERY_LOW_TEMPERATURE, Severity.SC_WARNING),
		]

	@contextmanager
	def temperature_configuration(self, checks):
		sensors = [(check.sensor, check.warm) for check in checks]
		boiler = self._programList['boiler']
		sensors.append((boiler.get_input_channel('backwardTemperature' if self.SEVERE else 'temperature'),
			20 if self.SEVERE else self.SOURCE_TEMPERATURE))
		if any(not sensor.is_mapped() for sensor, _ in sensors):
			raise RuntimeError('Не назначен необходимый датчик температурного теста')
		for name, channel in [('circuit', 'pump'), ('boiler', 'burner1')]:
			if not self._programList[name].get_output_channel(channel).is_mapped():
				raise RuntimeError(f'Не назначен выход {name}.{channel}')
		settings = self.settings()
		saved = [(program, kind, key, self.read_parameter(program, kind, key))
			for program, kind, key, _ in settings]
		attempted = []
		with ExitStack() as cleanup:
			cleanup.enter_context(preserved_inputs(self, [sensor for sensor, _ in sensors]))
			try:
				for sensor, value in sensors:
					self.set_sensor_value(sensor, value)
				for setting, original in zip(settings, saved):
					attempted.append(original)
					self.write_parameter(*setting)
				yield
			finally:
				self._cleanup_failed = True
				errors = []
				try:
					for original in reversed(attempted):
						try:
							self.write_parameter(*original)
						except Exception as error:
							errors.append(str(error))
				finally:
					# Restore inputs even when a parameter restoration failed.
					cleanup.close()
				if errors:
					raise RuntimeError('Не восстановлены параметры: ' + '; '.join(errors))
				self._cleanup_failed = False

	def input_is(self, check, value):
		actual = self.read_parameter(check.program, snc.ProgramType.PROGRAM,
			snc.ProgramParameterId.INPUT, index=0)
		return abs(actual - value) <= self.TEMPERATURE_TOLERANCE

	def change_temperature(self, check, value):
		check.changed_at = self.clock()
		self.set_sensor_value(check.sensor, value)
		if not self.wait_event(lambda: self.input_is(check, value), self.INPUT_TIMEOUT):
			raise RuntimeError(f'{check.name}: контроллер не получил температуру {value} °C')
		check.confirmed_at = self.clock()

	def validate_operating_state(self, checks):
		pump = self._programList['circuit'].get_output_channel('pump').get_value()
		if pump is None or pump == self.RELAY_OFF:
			raise RuntimeError('Насос контура должен оставаться включённым')
		for check in checks:
			if check.phase == 'done':
				continue
			expected = (check.cold if check.phase == 'cold' else
				check.intermediate if check.phase == 'intermediate' else check.warm)
			if not self.input_is(check, expected):
				raise RuntimeError(f'{check.name}: температура не удерживается на {expected} °C')
		for name in ('circuit',) if self.SEVERE else ('circuit', 'dhw'):
			expected = (self.CASCADE_SETPOINT if self.SEVERE else
				self.CIRCUIT_SETPOINT if name == 'circuit' else self.DHW_SETPOINT)
			actual = self.read_parameter(self._programList[name], snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE)
			if abs(actual - expected) > self.TEMPERATURE_TOLERANCE:
				raise RuntimeError(f'{name}: изменилась требуемая температура: {actual}')
		if self.SEVERE:
			cascade = self._programList['cascade']
			required = self.read_parameter(cascade, snc.ProgramType.TEMPERATURE_SOURCE,
				snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE)
			if abs(required - self.CASCADE_SETPOINT) > self.TEMPERATURE_TOLERANCE:
				raise RuntimeError('Каскад не сохраняет требуемую температуру')
			cold = {check.name for check in checks if check.phase == 'cold'}
			if 'cascade' in cold and self.read_parameter(cascade, snc.ProgramType.CASCADE_MANAGER,
					snc.CascadeManagerParameterId.REQUIRED_POWER) <= 0:
				raise RuntimeError('Во время недогрева каскад не запрашивает мощность')
			boiler_check = next(check for check in checks if check.name == 'boiler')
			if 'boiler' in cold and self.clock() < boiler_check.changed_at + boiler_check.delay - self.EARLY_TOLERANCE:
				burner = self._programList['boiler'].get_output_channel('burner1').get_value()
				if burner is None or burner == self.RELAY_OFF:
					raise RuntimeError('При недогреве первая ступень котла должна работать')

	def accept_entries(self, checks, entries):
		for entry in entries:
			for check in checks:
				if entry.param != check.program.get_id():
					continue
				if not self.SEVERE and entry.code == Code.MLC_PROGRAM_VERY_LOW_TEMPERATURE:
					check.invalid = True
					print_error(f'{check.name}: вместо небольшого недогрева возник сильный')
				if entry.code == check.code and check.phase == 'cold':
					check.cold_ok = (entry.severity == check.severity and not check.invalid
						and self.clock() >= check.changed_at + check.delay - self.EARLY_TOLERANCE
						and self.clock() <= check.confirmed_at + check.delay + self.LATE_TOLERANCE)
					print_log(f'{check.name}: недогрев — {"OK" if check.cold_ok else "FAIL"}')
					check.phase = 'normalize'
				elif check.recovery_code is not None and entry.code == check.recovery_code:
					if check.phase != 'recovery':
						check.recovery_invalid = True
						print_error(f'{check.name}: преждевременное сообщение восстановления')
					else:
						check.recovery_ok = (check.cold_ok and not check.invalid and not check.recovery_invalid
							and entry.severity == check.recovery_severity
							and self.clock() >= check.changed_at + check.recovery_delay - self.EARLY_TOLERANCE
							and self.clock() <= check.confirmed_at + self.RECOVERY_TIMEOUT)
						check.phase = 'done'
						print_log(f'{check.name}: восстановление — {"OK" if check.recovery_ok else "FAIL"}')

	def observe_checks(self, checks):
		next_observation = self.clock()
		while any(check.phase != 'done' for check in checks):
			entries = self._read_journal(self._journal_cursor)
			if entries is None:
				raise RuntimeError('Не удалось полностью прочитать журнал')
			if entries:
				self._journal_cursor = entries[-1]
			self.accept_entries(checks, entries)
			for check in checks:
				if check.phase == 'normalize':
					self.change_temperature(check, check.warm if check.intermediate is None else check.intermediate)
					check.phase = ('done' if check.recovery_code is None else
						'recovery' if check.intermediate is None else 'intermediate')
				elif check.phase == 'intermediate' and self.clock() >= check.confirmed_at + self.INTERMEDIATE_HOLD:
					self.change_temperature(check, check.warm)
					check.phase = 'recovery'
				elif check.phase in ('cold', 'recovery'):
					timeout = check.delay + self.LATE_TOLERANCE if check.phase == 'cold' else self.RECOVERY_TIMEOUT
					if self.clock() > check.confirmed_at + timeout:
						print_error(f'{check.name}: нет сообщения, этап {check.phase}')
						check.phase = 'done'
			if self.clock() >= next_observation:
				self.validate_operating_state(checks)
				next_observation = self.clock() + self.OBSERVATION_INTERVAL
			if self.wait(self.POLL_INTERVAL) is False:
				raise ThreadStoppedException('Ожидание журнала прервано')

	def run_temperature_test(self):
		self._status = 'FAIL'
		self._checklist_results = dict.fromkeys(('9.18', '9.19') if self.SEVERE else ('9.16', '9.17'), 'FAIL')
		self._cleanup_failed = False
		checks = []
		try:
			checks = self.make_checks()
			with self.temperature_configuration(checks):
				for check in checks:
					if not self.wait_event(lambda c=check: self.input_is(c, c.warm), self.INPUT_TIMEOUT):
						raise RuntimeError(f'{check.name}: не подтверждена исходная температура')
				if self.wait(self.BASELINE_HOLD) is False:
					raise ThreadStoppedException('Подготовка сценария прервана')
				if not self.snapshot_journal():
					return
				for check in checks:
					if self.SEVERE and check.name == 'boiler':
						# The boiler's own fault must not suppress cascade power before its log entry.
						if self.wait(self.GENERATOR_ALARM_STAGGER) is False:
							raise ThreadStoppedException('Подготовка котла прервана')
					self.change_temperature(check, check.cold)
				self.validate_operating_state(checks)
				self.observe_checks(checks)
		except ThreadStoppedException:
			raise
		except Exception as error:
			print_error(str(error))
		finally:
			if checks and not self._cleanup_failed:
				ids = list(self._checklist_results)
				self._checklist_results[ids[0]] = 'OK' if all(c.cold_ok and not c.invalid for c in checks) else 'FAIL'
				recoveries = [c for c in checks if c.recovery_code is not None]
				self._checklist_results[ids[1]] = 'OK' if recoveries and all(
					c.recovery_ok and not c.invalid and not c.recovery_invalid for c in recoveries) else 'FAIL'
			if all(v == 'OK' for v in self._checklist_results.values()):
				self._status = 'OK'
			else:
				self._status = 'FAIL'
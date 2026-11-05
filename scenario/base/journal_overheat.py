"""Black-box overheating checks using real firmware delays and shared cleanup."""

from consoleLog import print_error, print_log
from scenario.base.journal_temperature import JournalTemperatureScenario, TemperatureCheck
from scenario.scenario import ThreadStoppedException
import smartnet.constants as snc
from smartnet.message_log_constants import MessageLogCode as Code, SeverityCode as Severity


class JournalOverheatScenario(JournalTemperatureScenario):
	TARGET = 'circuit'
	OVERHEAT_DELAY = 2 * 60
	CIRCUIT_MAXIMUM = 70
	CIRCUIT_OVERHEAT_DELTA = 6
	BOILER_MAXIMUM = 75
	BOILER_COOLING_TEMPERATURE = 80
	BOILER_OVERHEAT_DELTA = 5
	BASELINE_HOLD = 40
	LATE_TOLERANCE = 60

	def get_required_programs(self):
		return {'circuit': snc.ProgramType.HEATING_CIRCUIT, 'boiler': snc.ProgramType.BOILER}

	def get_default_preset(self):
		return 'journal_low_temperature'

	def get_checklist_results(self):
		return {self.get_checklist_id(): self._status}

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
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, self.CIRCUIT_SETPOINT),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MINIMUM_FLOW_TEMPERATURE, self.CIRCUIT_MINIMUM),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE, self.CIRCUIT_MAXIMUM),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.ROOM_SENSOR_INFLUENCE, 0),
			(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.PRIORITY, 0),
			(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.TEMPERATURE_COMPENSATION, 0),
			(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.HEAT_EXTRICATION_ENABLED, 0),
		):
			settings.append((p['circuit'], kind, key, value))
		for key, value in (
			(snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION, 0),
			(snc.TemperatureGeneratorParameterId.MAXIMUM_TEMPERATURE, self.BOILER_MAXIMUM),
		):
			settings.append((p['boiler'], snc.ProgramType.TEMPERATURE_GENERATOR, key, value))
		settings.extend([
			(p['boiler'], snc.ProgramType.BOILER, snc.BoilerParameterId.WARMUP_TEMPERATURE, self.BOILER_WARMUP),
			(p['boiler'], snc.ProgramType.BOILER, snc.BoilerParameterId.BOILER_COOLING_TEMPERATURE,
			 self.BOILER_COOLING_TEMPERATURE),
		])
		return settings

	def make_checks(self):
		program = self._programList[self.TARGET]
		hot = (self.CIRCUIT_MAXIMUM + self.CIRCUIT_OVERHEAT_DELTA if self.TARGET == 'circuit'
			else self.BOILER_COOLING_TEMPERATURE + self.BOILER_OVERHEAT_DELTA)
		normal = self.CIRCUIT_SETPOINT if self.TARGET == 'circuit' else self.SOURCE_TEMPERATURE
		return [TemperatureCheck(self.TARGET, program, program.get_input_channel('temperature'),
			hot, normal, self.OVERHEAT_DELAY, Code.MLC_PROGRAM_VERY_HI_TEMPERATURE, Severity.SC_WARNING)]

	def validate_operating_state(self, checks):
		for check in checks:
			if check.phase == 'done':
				continue
			if not self.input_is(check, check.cold):
				raise RuntimeError(f'{check.name}: температура перегрева не удерживается')
			if check.name == 'circuit' and not self.pump_is_on():
				raise RuntimeError('Во время перегрева контура отключилась циркуляция')

	def pump_is_on(self):
		value = self._programList['circuit'].get_output_channel('pump').get_value()
		return value is not None and value != self.RELAY_OFF

	def accept_entries(self, checks, entries):
		for check in checks:
			for entry in entries:
				if entry.param != check.program.get_id() or entry.code != check.code or check.phase != 'cold':
					continue
				check.cold_ok = (entry.severity == check.severity
					and self.clock() >= check.changed_at + check.delay - self.EARLY_TOLERANCE
					and self.clock() <= check.confirmed_at + check.delay + self.LATE_TOLERANCE)
				check.phase = 'normalize'
				print_log(f'{check.name}: перегрев — {"OK" if check.cold_ok else "FAIL"}')

	def run_overheat_test(self):
		self._status = 'FAIL'
		self._cleanup_failed = False
		try:
			checks = self.make_checks()
			with self.temperature_configuration(checks):
				for check in checks:
					if not self.wait_event(lambda c=check: self.input_is(c, c.warm), self.INPUT_TIMEOUT):
						raise RuntimeError('Не подтверждена исходная температура')
				if self.TARGET == 'circuit' and not self.wait_event(self.pump_is_on, self.INPUT_TIMEOUT):
					raise RuntimeError('Не включился насос контура')
				if self.wait(self.BASELINE_HOLD) is False:
					raise ThreadStoppedException('Подготовка сценария прервана')
				if not self.snapshot_journal():
					return
				for check in checks:
					self.change_temperature(check, check.cold)
				self.validate_operating_state(checks)
				self.observe_checks(checks)
			# Success is assigned only after all parameters and inputs were restored.
			if all(check.cold_ok for check in checks):
				self._status = 'OK'
		except ThreadStoppedException:
			raise
		except Exception as error:
			print_error(str(error))
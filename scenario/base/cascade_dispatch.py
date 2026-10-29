"""Black-box dispatch checks. Expected behaviour is not a firmware emulator."""

from contextlib import contextmanager
from time import monotonic

from consoleLog import print_error, print_log
from scenario.base.cascade_manager import CascadeManagerScenario
from smartnet.cascade_monitor import CascadeMonitor
import smartnet.constants as snc
from smartnet.message import Message


class CascadeDispatchScenario(CascadeManagerScenario):
	BOILER_COUNT = 2
	DELAY_MINUTES = 0
	TEST_FAULTS = False
	SETPOINT = 50
	PROPORTIONAL_BAND = 20
	POWER_TOLERANCE = 3
	OUTPUT_PROBE_INTERVAL = 5
	SETTLING_TIMEOUT = 25
	FAULT_DETECTION_TIMEOUT = 90
	REPLACEMENT_TIMEOUT = 15
	TIMING_MARGIN = 5
	POLL_PERIOD = 1
	CANCEL_PULSE_DURATION = 20
	SECONDS_PER_MINUTE = 60
	clock = staticmethod(monotonic)

	def get_required_programs(self):
		return {
			'cascade': snc.ProgramType.CASCADE_MANAGER,
			**{f'boiler_{index + 1}': snc.ProgramType.BOILER for index in range(self.BOILER_COUNT)},
			'dhw': snc.ProgramType.DHW,
		}

	def boilers(self):
		return [self._programList[f'boiler_{index + 1}'] for index in range(self.BOILER_COUNT)]

	def settings(self):
		cascade = self._programList['cascade']
		parameter = snc.CascadeManagerParameterId
		values = (
			(parameter.PARAM_I_FACTOR, 0), (parameter.PARAM_D_FACTOR, 0),
			(parameter.PARAM_P_FACTOR, self.PROPORTIONAL_BAND),
			(parameter.WORK_FUNCTION, 0), (parameter.ROTATION_TYPE, 0),
			(parameter.TEMPERATURE_OFFSET, 0), (parameter.MINIMUM_REQUIRED_TEMPERATURE, 0),
			(parameter.MAXIMUM_REQUIRED_TEMPERATURE, 90),
			(parameter.NEXT_TEMPERATURE_SRC_ON_DELAY, self.DELAY_MINUTES * self.SECONDS_PER_MINUTE),
		)
		settings = [(cascade, snc.ProgramType.CASCADE_MANAGER, key, value) for key, value in values]
		dhw = self._programList['dhw']
		settings.extend([
			(dhw, snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT, self.SETPOINT),
			(dhw, snc.ProgramType.DHW, snc.DhwParameterId.WORK_MODE, 0),
			(dhw, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.TEMPERATURE_COMPENSATION, 0),
		])
		for boiler in self.boilers():
			settings.extend([
				(boiler, snc.ProgramType.TEMPERATURE_GENERATOR,
				 snc.TemperatureGeneratorParameterId.PUMP_OFF_DELAY, 0),
				(boiler, snc.ProgramType.TEMPERATURE_GENERATOR,
				 snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION, 0),
			])
		return settings

	def validate_topology(self):
		ids = [boiler.get_id() for boiler in self.boilers()]
		if len(set(ids)) != self.BOILER_COUNT:
			raise RuntimeError('Повторяющиеся ID котлов')
		for boiler in self.boilers():
			if any(boiler.get_input_channel(key).is_mapped() for key in ('temperature', 'backwardTemperature', 'outsideRequest')):
				raise RuntimeError('Котёл не должен иметь локальное регулирование или внешний запрос')
			if any(boiler.get_output_channel(key).is_mapped() for key in ('burner1', 'burner2')):
				raise RuntimeError('Тест требует только модулируемый выход мощности')
			if not all(boiler.get_output_channel(key).is_mapped() for key in ('power', 'pump')):
				raise RuntimeError('Не найдены выходы мощности и насоса котла')
			if not boiler.get_input_channel('error').is_mapped():
				raise RuntimeError('Не найден аварийный вход котла')

	def sources_are_ready(self):
		powers = []
		for index, boiler in enumerate(self.boilers()):
			cascade = self._programList['cascade']
			if self.read_parameter(cascade, snc.ProgramType.CASCADE_MANAGER,
				snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID, index) != boiler.get_id():
				return False
			powers.append(self.read_parameter(cascade, snc.ProgramType.CASCADE_MANAGER,
				snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_POWER, index))
		return all(power > 0 and power == powers[0] for power in powers)

	@contextmanager
	def alarm_configuration(self):
		originals = []
		for boiler in self.boilers():
			sensor = boiler.get_input_channel('error')
			originals.append((sensor, sensor.get_value(), sensor.isShort(), sensor.isOpen(),
				sensor.isManual(), sensor in self._manualSensorsList))
		try:
			for sensor, *_ in originals:
				self.set_sensor_value(sensor, 'open')
			yield
		finally:
			for sensor, value, short, opened, manual, tracked in originals:
				try:
					sensor.set_manual(True)
					sensor.set_value(value, True)
					if short:
						sensor.setShort(True)
					elif opened:
						sensor.setOpen(True)
				except Exception as exc:
					print_error(f'Не восстановлен аварийный вход: {exc}')
					self._status = 'FAIL'
				finally:
					try:
						sensor.set_manual(manual)
					except Exception as exc:
						print_error(f'Не восстановлен режим аварийного входа: {exc}')
						self._status = 'FAIL'
					if not tracked and sensor in self._manualSensorsList:
						self._manualSensorsList.remove(sensor)

	def await_condition(self, condition, timeout, description, guard=None, stable=None, details=None):
		"""Use monotonic deadlines; never hide a transient violation in a guard."""
		deadline = self.clock() + timeout
		stable_since = None
		stable = self.STABILITY_DURATION if stable is None else stable
		matched = False
		while self.clock() <= deadline:
			if guard:
				guard()
			matched = condition()
			now = self.clock()
			if now > deadline:
				break
			if matched:
				if stable_since is None:
					stable_since = now
				if now - stable_since >= stable:
					return
			else:
				stable_since = None
			self.wait(self.POLL_PERIOD)
		if details is not None:
			print_error(f'Тайм-аут: {description}; условие сейчас={matched}, '
				f'устойчиво с={stable_since}; {details()}')
		raise RuntimeError(description)

	def hold_condition(self, condition, duration, description, guard=None):
		deadline = self.clock() + duration
		while True:
			if guard:
				guard()
			if not condition():
				raise RuntimeError(description)
			if self.clock() >= deadline:
				return
			self.wait(self.POLL_PERIOD)

	def expected_powers(self, demand, failed=()):
		# Demand is a percentage of INSTALLED capacity, not remaining capacity.
		remaining = self.BOILER_COUNT * demand
		result = {}
		for boiler in self.boilers():
			boiler_id = boiler.get_id()
			power = 0 if boiler_id in failed else min(100, remaining)
			result[boiler_id] = power
			remaining -= power
		return result

	def request_output_states(self):
		"""Request current output values without waiting for any CAN response."""
		for boiler in self.boilers():
			for channel in ('power', 'pump'):
				Message(snc.ProgramType.REMOTE_CONTROL, boiler.get_id(),
					snc.RemoteControlFunction.GET_PARAMETER_VALUE, snc.RequestFlag.REQUEST,
					[snc.ProgramType.PROGRAM, snc.ProgramParameterId.OUTPUT,
					 boiler.get_output_channel(channel).get_id()]).send()

	def probe_outputs(self):
		now = self.clock()
		if (getattr(self, '_last_output_probe', None) is None
			or now - self._last_output_probe >= self.OUTPUT_PROBE_INTERVAL):
			self._last_output_probe = now
			self.request_output_states()

	@staticmethod
	def output_power_percent(signal):
		return max(0.0, min(100.0, (signal - 1) * 100.0 / 253))

	def outputs_match(self, expected, since):
		self.fault_guard()
		self.probe_outputs()
		reports = self.monitor.output_snapshot()
		latest = {(report.boiler_id, report.index): report for report in reports if report.time >= since}
		self._command_mismatch = None
		for boiler in self.boilers():
			boiler_id = boiler.get_id()
			power = expected[boiler_id]
			output_index = boiler.get_power_output().get_id()
			pump_index = boiler.get_pump().get_id()
			output = latest.get((boiler_id, output_index))
			pump = latest.get((boiler_id, pump_index))
			if output is None or pump is None:
				self._command_mismatch = (f'котёл {boiler_id}: нет подтверждения выходов после {since:.1f}: '
					f'мощность={output}, насос={pump}')
				return False
			actual = self.output_power_percent(output.value)
			if abs(actual - power) > self.POWER_TOLERANCE:
				self._command_mismatch = f'котёл {boiler_id}: выход {actual:.1f}% вместо {power}%'
				return False
			if power == 0 and output.value != 0:
				self._command_mismatch = f'котёл {boiler_id}: при 0% выходной сигнал {output.value} вместо 0'
				return False
			if pump.value != (255 if power > 0 else 0):
				self._command_mismatch = (f'котёл {boiler_id}: насос {pump.value} '
					f'вместо {255 if power > 0 else 0}')
				return False
		return True

	def commands_match(self, expected, since):
		"""Compatibility alias for callers of the old dispatch check."""
		return self.outputs_match(expected, since)

	def dispatch_diagnostics(self, expected, since):
		commands, _ = self.monitor.snapshot()
		reports = self.monitor.output_snapshot()
		now = self.clock()
		states = []
		for boiler in self.boilers():
			boiler_id = boiler.get_id()
			recent = [command for command in commands if command.boiler_id == boiler_id]
			command = recent[-1] if recent else None
			output = boiler.get_power_output()
			pump = boiler.get_pump()
			if command is None:
				states.append(f'{boiler_id}: ожидается {expected[boiler_id]}%, команд нет')
			else:
				states.append(f'{boiler_id}: ожидается {expected[boiler_id]}%, '
					f'последняя команда={command}, возраст={now - command.time:.1f} с')
			states.append(f'{boiler_id}: выход={output.get_value()} ({boiler.get_power_output_percent()}%), '
				f'свежий={output.valueIsUpToDate()}; насос={pump.get_value()}, свежий={pump.valueIsUpToDate()}')
			states.append(f'{boiler_id}: последние отчёты выходов '
				f'{[report for report in reports if report.boiler_id == boiler_id][-6:]}')
		return (f'последняя причина={self._command_mismatch}; коллектор={self.collector.get_value()} °C, '
			f'начало={since:.1f}, сейчас={now:.1f}; '
			+ '; '.join(states))

	def set_demand(self, demand):
		started = self.clock()
		temperature = self.SETPOINT - self.PROPORTIONAL_BAND * demand / 100
		if demand == 0:
			temperature = self.SETPOINT + self.TIMING_MARGIN
		self.set_sensor_value(self.collector, temperature)
		print_log(f'Запрос мощности каскада {demand}%: коллектор задан={temperature} °C, '
			f'прочитан={self.collector.get_value()} °C, время={started:.1f}')
		return started

	def check_dispatch(self, demand, timeout=None, guard=None, since=None, failed=()):
		if since is None:
			since = self.set_demand(demand)
		expected = self.expected_powers(demand, failed)
		self.await_condition(lambda: self.outputs_match(expected, since),
			self.SETTLING_TIMEOUT if timeout is None else timeout,
			f'Неверные выходы котлов: запрос {demand}%, ожидается {expected}', guard,
			details=lambda: self.dispatch_diagnostics(expected, since))
		if len(failed) < self.BOILER_COUNT and not self.required_temperature_is(self.SETPOINT):
			raise RuntimeError('Пропал температурный запрос потребителя')
		if not failed and abs(self.read_required_power() - demand) > self.POWER_TOLERANCE:
			raise RuntimeError('Неверная требуемая мощность каскада')

	def delay_guard(self, since, active_count):
		reports = self.monitor.output_snapshot()
		delay = self.DELAY_MINUTES * self.SECONDS_PER_MINUTE
		ids = [boiler.get_id() for boiler in self.boilers()]
		active_indices = {boiler.get_id(): (boiler.get_power_output().get_id(), boiler.get_pump().get_id())
			for boiler in self.boilers()}
		for report in reports:
			if report.time < since or report.index not in active_indices.get(report.boiler_id, ()) or report.value == 0:
				continue
			index = ids.index(report.boiler_id)
			if index >= active_count:
				raise RuntimeError(f'Включён лишний котёл {report.boiler_id}')
			if index == active_count - 1 and active_count > 1:
				if report.time < since + delay - self.TIMING_MARGIN:
					raise RuntimeError(f'Раннее включение котла {report.boiler_id}')

	def exercise_stages(self):
		self.check_dispatch(0)
		# Last active boiler stays well below 50%, resetting stage availability.
		loads = [round(100 * (count - 0.75) / self.BOILER_COUNT)
			for count in range(1, self.BOILER_COUNT + 1)]
		for count, demand in enumerate(loads, 1):
			since = self.set_demand(demand)
			self.check_dispatch(demand, self.DELAY_MINUTES * self.SECONDS_PER_MINUTE + self.SETTLING_TIMEOUT,
				lambda: self.delay_guard(since, count), since)
		self.check_dispatch(100)
		for demand in reversed(loads):
			self.check_dispatch(demand)
		self.check_dispatch(0)
		if self.DELAY_MINUTES:
			self.exercise_cancelled_stage(loads[0], loads[1])
		self.check_dispatch(loads[0])
		self.check_dispatch(0)

	def exercise_cancelled_stage(self, low, high):
		self.check_dispatch(low)
		since = self.set_demand(high)
		first_id = self.boilers()[0].get_id()
		power_index = self.boilers()[0].get_power_output().get_id()
		def first_boiler_at_full_power():
			self.probe_outputs()
			return any(r.time >= since and r.boiler_id == first_id and r.index == power_index
				and self.output_power_percent(r.value) >= 95 for r in self.monitor.output_snapshot())
		self.await_condition(
			first_boiler_at_full_power,
			self.SETTLING_TIMEOUT, 'Первый котёл не вышел на полную мощность',
			lambda: self.delay_guard(since, 1), stable=0)
		self.hold_condition(lambda: True, self.CANCEL_PULSE_DURATION,
			'Прерван короткий запрос', lambda: self.delay_guard(since, 1))
		self.check_dispatch(low, guard=lambda: self.delay_guard(since, 1))
		low_since = self.clock()
		self.hold_condition(lambda: self.outputs_match(self.expected_powers(low), low_since),
			self.DELAY_MINUTES * self.SECONDS_PER_MINUTE + self.TIMING_MARGIN,
			'Отложенное включение после отмены запроса', lambda: self.delay_guard(since, 1))
		# A new request must receive a full, fresh delay, not the old remainder.
		since = self.set_demand(high)
		self.check_dispatch(high, self.DELAY_MINUTES * self.SECONDS_PER_MINUTE + self.SETTLING_TIMEOUT,
			lambda: self.delay_guard(since, 2), since)
		self.check_dispatch(0)

	def fault_guard(self):
		reports = self.monitor.output_snapshot()
		commands, _ = self.monitor.snapshot()
		power_indices = {boiler.get_id(): boiler.get_power_output().get_id() for boiler in self.boilers()}
		for command in commands:
			confirmed = getattr(self, '_fault_confirmations', {}).get(command.boiler_id)
			if (confirmed is not None and command.time >= confirmed + self.REPLACEMENT_TIMEOUT
				and command.power > 0):
				raise RuntimeError(f'Каскад запрашивает {command.power}% у аварийного котла '
					f'{command.boiler_id} спустя {command.time - confirmed:.1f} с после подтверждения аварии')
		for report in reports:
			confirmed = getattr(self, '_fault_confirmations', {}).get(report.boiler_id)
			if (confirmed is not None and report.time >= confirmed + self.REPLACEMENT_TIMEOUT
				and report.index == power_indices.get(report.boiler_id) and report.value):
				raise RuntimeError(f'Работает аварийный котёл {report.boiler_id}')

	def set_faults(self, failed):
		started = self.clock()
		previous = getattr(self, '_failed', None)
		ids = {boiler.get_id() for boiler in self.boilers()}
		changed = ids if previous is None else previous.symmetric_difference(failed)
		confirmations = getattr(self, '_fault_confirmations', {})
		self._fault_confirmations = {key: value for key, value in confirmations.items() if key in failed}
		reports = {}
		for boiler in self.boilers():
			self.set_sensor_value(boiler.get_input_channel('error'),
				'short' if boiler.get_id() in failed else 'open')
		def reported():
			properties = self.monitor.snapshot()[1]
			for boiler_id in changed:
				entry = properties.get(boiler_id)
				if entry and entry[0] >= started and bool(entry[1]) == (boiler_id in failed):
					reports.setdefault(boiler_id, entry[0])
					if boiler_id in failed:
						self._fault_confirmations.setdefault(boiler_id, entry[0])
			self.fault_guard()
			return changed.issubset(reports)
		self.await_condition(reported, self.FAULT_DETECTION_TIMEOUT,
			f'Не получены свойства котлов после смены аварий: {failed}', stable=0)
		self._failed = set(failed)
		# Every property frame was visible to the manager on the same bus.
		return max(reports.values(), default=started)

	def check_fault_dispatch(self, demand, failed):
		confirmed = self.set_faults(failed)
		remaining = self.REPLACEMENT_TIMEOUT - (self.clock() - confirmed)
		self.check_dispatch(demand, max(0, remaining), since=confirmed, failed=failed)
		error = self.read_parameter(self._programList['cascade'], snc.ProgramType.TEMPERATURE_SOURCE,
			snc.TemperatureSourceParameterId.ERROR_STATE)
		if bool(error) != (len(failed) == self.BOILER_COUNT):
			raise RuntimeError('Неверный признак «все источники неисправны»')

	def exercise_faults(self):
		ids = [boiler.get_id() for boiler in self.boilers()]
		low = round(50 / self.BOILER_COUNT)
		self.set_faults(set())
		for index, boiler_id in enumerate(ids):
			print_log(f'Авария котла {boiler_id} до запроса тепла')
			self.check_dispatch(0)
			self.check_fault_dispatch(0, {boiler_id})
			self.check_dispatch(low, failed={boiler_id})
			self.check_fault_dispatch(low, set())
			# Put this particular boiler into operation before failing it.
			demand = round(100 * (index + 0.25) / self.BOILER_COUNT)
			self.check_dispatch(0)
			self.check_dispatch(demand,
				self.BOILER_COUNT * self.DELAY_MINUTES * self.SECONDS_PER_MINUTE + self.SETTLING_TIMEOUT)
			print_log(f'Авария работающего котла {boiler_id}')
			self.check_fault_dispatch(demand, {boiler_id})
			self.check_fault_dispatch(demand, set())
		self.check_dispatch(0)
		self.check_dispatch(low)
		for count in range(1, self.BOILER_COUNT + 1):
			self.check_fault_dispatch(low, set(ids[:count]))
		# Recover only the LAST boiler: catches checking only source[0].
		self.check_fault_dispatch(low, set(ids[:-1]))
		self.check_fault_dispatch(low, set())
		self.check_dispatch(0)

	def execute(self):
		self._status = 'FAIL'
		self.validate_topology()
		self.collector = self._programList['cascade'].get_input_channel('temperature')
		dhw_sensor = self._programList['dhw'].get_temperature()
		monitor = CascadeMonitor(self._programList['cascade'].get_id(),
			[boiler.get_id() for boiler in self.boilers()], self.clock)
		self.monitor = monitor
		try:
			with monitor, self.test_configuration(self.settings(), (self.collector, dhw_sensor)), self.alarm_configuration():
				self.set_sensor_value(dhw_sensor, 20)
				self.set_demand(0)
				self.require_stable(self.sources_are_ready, 'Не обнаружены котлы одинаковой мощности')
				if self.TEST_FAULTS:
					self.exercise_faults()
				else:
					self.set_faults(set())
					self.exercise_stages()
				self._status = 'OK'
		except RuntimeError as exc:
			self._status = 'FAIL'
			print_error(str(exc))
			try:
				commands, properties = monitor.snapshot()
				print_error(f'Свойства источников: {properties}; последние команды: {commands[-20:]}')
				print_error(f'Последние выходы котлов: {monitor.output_snapshot()[-40:]}; '
					f'ошибка разбора команды (диагностика): {monitor.command_error}')
			except RuntimeError as monitor_error:
				print_error(str(monitor_error))
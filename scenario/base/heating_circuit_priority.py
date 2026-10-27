"""Heating circuit priority requests observed on the controller CAN bus."""

import math

import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter
from consoleLog import print_error
from scenario.base.consumer_priority import ConsumerPriorityCapture
from scenario.scenario import Scenario as Parent
from scenario.steps import ScenarioSteps, preserved_inputs


class HeatingCircuitPriorityScenario(ConsumerPriorityCapture, Parent):
	REQUIRED_TEMPERATURE = 40
	SOURCE_TEMPERATURE = 30
	OPENING_BANDS = (5, 10)
	DEFICIT_MARGIN = 1
	PUMP_ALWAYS_ON = 2
	DELIVERY_TIMEOUT = 60
	STABILIZATION_DURATION = 5
	REQUEST_TIMEOUT = 45
	# GIVE_WAY is broadcast every 10 seconds: observe more than two periods.
	NO_REQUEST_DURATION = 25

	def get_default_preset(self):
		return 'heating_circuit_priority'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'mixed': snc.ProgramType.HEATING_CIRCUIT,
			'direct': snc.ProgramType.HEATING_CIRCUIT,
			'mixed_without_sensor': snc.ProgramType.HEATING_CIRCUIT,
			'boiler': snc.ProgramType.BOILER,
		}

	def _get_priority_program(self):
		return self._circuit

	def _read_parameter(self, program, program_type, parameter_id, index=None):
		parameter = RemoteControlParameter(
			programType=program_type, parameterId=parameter_id,
			programId=program.get_id(), parameterIndex=index,
		)
		if not parameter.read():
			raise RuntimeError(f'Не прочитан параметр {program_type}/{parameter_id}')
		value = parameter.get_value()
		if not isinstance(value, (int, float)) or not math.isfinite(value):
			raise RuntimeError(f'Некорректный параметр {program_type}/{parameter_id}: {value}')
		return value

	def _write_parameter(self, program, program_type, parameter_id, value):
		parameter = RemoteControlParameter(
			programType=program_type, parameterId=parameter_id,
			programId=program.get_id(), parameterValue=value,
		)
		if not parameter.write():
			raise RuntimeError(f'Не записан параметр {program_type}/{parameter_id}')
		if self._read_parameter(program, program_type, parameter_id) != value:
			raise RuntimeError(f'Не подтверждён параметр {program_type}/{parameter_id}: {value}')

	def _settings(self):
		settings = []
		for program in self._programList.values():
			settings.extend([
				(program, snc.ProgramType.PROGRAM, snc.ProgramParameterId.TRAINING_ENABLED, 0),
				(program, snc.ProgramType.PROGRAM, snc.ProgramParameterId.MANUAL_MODE_ENABLED, 0),
			])
		for name in ('mixed', 'direct', 'mixed_without_sensor'):
			program = self._programList[name]
			settings.extend((program, program_type, parameter_id, value) for program_type, parameter_id, value in (
				(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.HEAT_CALCULATION_MODE,
				 snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE),
				(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MINIMUM_FLOW_TEMPERATURE, 5),
				(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE, 90),
				(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE,
				 self.REQUIRED_TEMPERATURE),
				(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.ROOM_SENSOR_INFLUENCE, 0),
				(snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.PUMP_MODE, self.PUMP_ALWAYS_ON),
				(snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.VALVE_OPEN_PROPORTIONAL_BAND,
				 self.OPENING_BANDS[0]),
				(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.PRIORITY, 5),
				(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.TEMPERATURE_COMPENSATION, 0),
				(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.HEAT_EXTRICATION_ENABLED, 0),
			))
		return settings

	def _validate_topology(self):
		ids = [program.get_id() for program in self._programList.values()]
		if len(ids) != len(set(ids)):
			raise RuntimeError('Повторяющиеся ID программ')
		for name, scheme, has_sensor in (
			('mixed', 'CIRCUIT_MIXED', True),
			('direct', 'CIRCUIT_DIRECT', False),
			('mixed_without_sensor', 'CIRCUIT_MIXED', False),
		):
			program = self._programList[name]
			if self._read_parameter(program, snc.ProgramType.PROGRAM,
					snc.ProgramParameterId.SCHEME) != snc.ProgramScheme[scheme]:
				raise RuntimeError(f'{name}: неверная схема контура')
			if program.get_input_channel('temperature').is_mapped() != has_sensor:
				raise RuntimeError(f'{name}: неверная привязка датчика подачи')
			if self._read_parameter(program, snc.ProgramType.CONSUMER,
					snc.ConsumerParameterId.GENERATOR_ID) != self._programList['boiler'].get_id():
				raise RuntimeError(f'{name}: неверный источник тепла')
			if not program.get_output_channel('pump').is_mapped():
				raise RuntimeError(f'{name}: не назначен насос')
			if name != 'direct' and not program.get_output_channel('analogValve').is_mapped():
				raise RuntimeError(f'{name}: не назначен смеситель')
			if any(program.get_input_channel(key).is_mapped()
					for key in ('thermostat', 'outsideRequest', 'pumpControl')):
				raise RuntimeError(f'{name}: посторонние входы могут влиять на запрос тепла')
		if not self._source_sensor.is_mapped():
			raise RuntimeError('Не назначен датчик котла')

	def _conditions_match(self, flow):
		if self._read_parameter(self._circuit, snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE) != self.REQUIRED_TEMPERATURE:
			return False
		if self._read_parameter(self._programList['boiler'], snc.ProgramType.PROGRAM,
				snc.ProgramParameterId.INPUT, self._source_sensor.get_id()) != self.SOURCE_TEMPERATURE:
			return False
		if flow is not None:
			# Exact comparison is required at the strict priority threshold.
			return self._read_parameter(self._circuit, snc.ProgramType.PROGRAM,
				snc.ProgramParameterId.INPUT, self._flow_sensor.get_id()) == flow
		return True

	def _observe(self, name, flow, expect_request):
		self._circuit = self._programList[name]
		if flow is not None:
			self.set_sensor_value(self._flow_sensor, flow)
		steps = ScenarioSteps(self)
		steps.expect(f'{name}: подтверждаем запрос тепла и входные температуры',
			lambda: self._conditions_match(flow), self.DELIVERY_TIMEOUT,
			hold=self.STABILIZATION_DURATION)
		self._begin_priority_capture()
		try:
			if expect_request:
				def request_received():
					if not self._conditions_match(flow):
						raise RuntimeError('Условия запроса приоритета изменились')
					return self._has_priority_event(snc.ConsumerFunction['GIVE_WAY'])
				steps.expect(f'{name}: ожидаем GIVE_WAY', request_received, self.REQUEST_TIMEOUT)
			else:
				steps.expect(f'{name}: GIVE_WAY отсутствует',
					lambda: self._conditions_match(flow)
					and not self._has_priority_event(snc.ConsumerFunction['GIVE_WAY']),
					self.DELIVERY_TIMEOUT, hold=self.NO_REQUEST_DURATION)
		finally:
			self._end_priority_capture()

	def _check_threshold(self):
		for band in self.OPENING_BANDS:
			self._write_parameter(self._programList['mixed'], snc.ProgramType.HEATING_CIRCUIT,
				snc.HeatingCircuitParameterId.VALVE_OPEN_PROPORTIONAL_BAND, band)
			self._observe('mixed', self.REQUIRED_TEMPERATURE - band, False)
			self._observe('mixed', self.REQUIRED_TEMPERATURE - band - self.DEFICIT_MARGIN, True)

	def _check_without_sensor(self):
		# Positive control: a silent bus must not pass the negative checks.
		self._observe('mixed', self.REQUIRED_TEMPERATURE - self.OPENING_BANDS[0] - self.DEFICIT_MARGIN, True)
		self.set_sensor_value(self._flow_sensor, self.REQUIRED_TEMPERATURE)
		for name in ('direct', 'mixed_without_sensor'):
			self._observe(name, None, False)

	def _run_priority_test(self, without_sensor=False):
		self._status = 'FAIL'
		attempted = []
		try:
			self._flow_sensor = self._programList['mixed'].get_input_channel('temperature')
			self._source_sensor = self._programList['boiler'].get_input_channel('temperature')
			self._validate_topology()
			settings = self._settings()
			originals = [(program, program_type, parameter_id,
				self._read_parameter(program, program_type, parameter_id))
				for program, program_type, parameter_id, _ in settings]
			for sensor in (self._flow_sensor, self._source_sensor):
				value = sensor.get_value()
				if (not isinstance(value, (int, float)) or not math.isfinite(value)
						or sensor.isShort() or sensor.isOpen()):
					raise RuntimeError('Исходные датчики подачи и котла должны быть исправны')
			with preserved_inputs(self, [self._flow_sensor, self._source_sensor]):
				try:
					# Avoid a transient under-temperature request during configuration.
					self.set_sensor_value(self._flow_sensor, self.REQUIRED_TEMPERATURE)
					self.set_sensor_value(self._source_sensor, self.SOURCE_TEMPERATURE)
					for setting, original in zip(settings, originals):
						attempted.append(original)
						self._write_parameter(*setting)
					if without_sensor:
						self._check_without_sensor()
					else:
						self._check_threshold()
					self._status = 'OK'
				finally:
					try:
						self._end_priority_capture()
					finally:
						for original in reversed(attempted):
							try:
								self._write_parameter(*original)
							except Exception as error:
								self._status = 'FAIL'
								print_error(f'Не восстановлен параметр контура: {error}')
		except Exception as error:
			self._status = 'FAIL'
			print_error(str(error))
		finally:
			self._end_priority_capture()
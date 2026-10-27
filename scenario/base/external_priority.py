"""Exercise consumers receiving another program's CAN priority broadcast."""

from contextlib import contextmanager
import math
import time

from consoleLog import print_error
from scenario.scenario import Scenario as Parent
from scenario.steps import ScenarioSteps, preserved_inputs
import smartnet.constants as snc
from smartnet.message import Message
from smartnet.remoteControl import RemoteControlParameter


class ExternalPriorityScenario(Parent):
	SENDER_ID = 250  # Different from every program in the selected presets.
	LOCAL_PRIORITY = 5
	HIGH_PRIORITY = 10
	NORMAL_OUTDOOR = 15
	DELIVERY_TIMEOUT = 60
	PUMP_TIMEOUT = 100  # Heating circuit has a one-minute pump-off delay.
	HOLD_DURATION = 8
	PUMP_DELAY_MARGIN = 70  # Longer than the heating circuit's one-minute off delay.
	REFRESH_PERIOD = 10  # Firmware forgets an unrefreshed GIVE_WAY after 60 s.
	MODE_COMFORT = 0
	MODE_ON = 1

	# Set by the concrete scenario: dhw, snow, mixed, direct or pool.
	TARGET = None
	PRESET = None

	def get_default_preset(self):
		return self.PRESET

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		if self.TARGET in ('mixed', 'direct'):
			return {
				'mixed': snc.ProgramType.HEATING_CIRCUIT,
				'direct': snc.ProgramType.HEATING_CIRCUIT,
				'mixed_without_sensor': snc.ProgramType.HEATING_CIRCUIT,
				'boiler': snc.ProgramType.BOILER,
				'oat': snc.ProgramType.OUTDOOR_SENSOR,
			}
		program_type = {'dhw': snc.ProgramType.DHW, 'snow': snc.ProgramType.SNOWMELT,
			'pool': snc.ProgramType.POOL}[self.TARGET]
		result = {'consumer': program_type, 'boiler': snc.ProgramType.BOILER}
		if self.TARGET == 'snow':
			result['oat'] = snc.ProgramType.OUTDOOR_SENSOR
		return result

	def _read(self, program_type, parameter_id, index=None):
		parameter = RemoteControlParameter(programType=program_type, parameterId=parameter_id,
			programId=self._consumer.get_id(), parameterIndex=index)
		if not parameter.read():
			raise RuntimeError(f'Не прочитан параметр {program_type}/{parameter_id}')
		value = parameter.get_value()
		if not isinstance(value, (int, float)) or not math.isfinite(value):
			raise RuntimeError(f'Некорректный параметр {program_type}/{parameter_id}: {value}')
		return value

	def _write(self, program_type, parameter_id, value):
		parameter = RemoteControlParameter(programType=program_type, parameterId=parameter_id,
			programId=self._consumer.get_id(), parameterValue=value)
		if not parameter.write() or self._read(program_type, parameter_id) != value:
			raise RuntimeError(f'Не подтверждена запись {program_type}/{parameter_id}: {value}')

	@contextmanager
	def _preserved_parameters(self):
		originals = []
		try:
			def set_parameter(program_type, parameter_id, value):
				originals.append((program_type, parameter_id, self._read(program_type, parameter_id)))
				self._write(program_type, parameter_id, value)
			yield set_parameter
		finally:
			for program_type, parameter_id, value in reversed(originals):
				try:
					self._write(program_type, parameter_id, value)
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен параметр {program_type}/{parameter_id}: {error}')

	def _send(self, function, data):
		Message(programType=snc.ProgramType.CONSUMER, programId=0,
			functionId=snc.ConsumerFunction[function], request=snc.RequestFlag.REQUEST,
			data=data).send()

	def _priority(self, priority=None, generator_id=None):
		if priority is None:
			self._send('PROCEED', [self.SENDER_ID, self._sent_priority, self._sent_generator_id])
			self._active_priority = None
			return
		self._sent_priority = priority
		self._sent_generator_id = self._generator_id if generator_id is None else generator_id
		self._active_priority = priority
		self._last_request = time.monotonic()
		self._send('GIVE_WAY', [self.SENDER_ID, priority, self._sent_generator_id])

	def _refresh(self):
		if self._active_priority is not None and time.monotonic() - self._last_request >= self.REFRESH_PERIOD:
			self._priority(self._active_priority, self._sent_generator_id)
		if self._cooling and time.monotonic() - self._last_cooling >= self.REFRESH_PERIOD:
			self._cool(True)

	def _cool(self, enabled):
		self._cooling = enabled
		self._last_cooling = time.monotonic()
		self._send('SET_COOLING', [self._generator_id, int(enabled)])

	def _expect(self, title, condition, timeout=None, hold=0):
		def refreshed():
			self._refresh()
			return condition()
		ScenarioSteps(self).expect(title, refreshed, timeout or self.DELIVERY_TIMEOUT, hold=hold)

	def _pump_on(self, channel):
		value = self._consumer.get_output_channel(channel).get_value()
		if value is None:
			raise RuntimeError(f'Не прочитано состояние насоса {channel}')
		return value != self.RELAY_OFF

	def _pump_off(self, channel):
		return not self._pump_on(channel)

	def _validate(self):
		self._consumer = self._programList.get(self.TARGET) if self.TARGET in ('mixed', 'direct') else self._programList.get('consumer')
		if self._consumer is None or 'boiler' not in self._programList:
			raise RuntimeError('Не найдены потребитель или генератор')
		self._generator_id = self._programList['boiler'].get_id()
		ids = [program.get_id() for program in self._programList.values()]
		if (len(ids) != len(set(ids)) or self.SENDER_ID in ids
				or self._read(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID) != self._generator_id):
			raise RuntimeError('Некорректная топология внешнего запроса')
		channels = {'dhw': ('supplyPump',), 'snow': ('primaryPump', 'secondaryPump'),
			'mixed': ('pump', 'analogValve'), 'direct': ('pump',), 'pool': ()}[self.TARGET]
		for channel in channels:
			if not self._consumer.get_output_channel(channel).is_mapped():
				raise RuntimeError(f'Не назначен выход {channel}')
		if self.TARGET in ('mixed', 'direct'):
			scheme = 'CIRCUIT_MIXED' if self.TARGET == 'mixed' else 'CIRCUIT_DIRECT'
			if self._read(snc.ProgramType.PROGRAM, snc.ProgramParameterId.SCHEME) != snc.ProgramScheme[scheme]:
				raise RuntimeError('Не та схема отопительного контура')
			if self.TARGET == 'direct' and any(self._consumer.get_output_channel(key).is_mapped()
					for key in ('analogValve', 'tptValveOpen', 'tptValveClose', 'thermomotor')):
				raise RuntimeError('Прямой контур имеет управление смесителем')

	def _sensors(self):
		if self.TARGET == 'dhw':
			return [self._consumer.get_temperature(),
				self._programList['boiler'].get_input_channel('temperature')]
		if self.TARGET == 'pool':
			return [self._consumer.get_temperature()]
		if self.TARGET == 'snow':
			return [self._consumer.getDirectFlowTemperature(),
				self._consumer.getBackwardFlowTemperature(), self._consumer.getPlateTemperature(),
				self._programList['oat'].getOutdoorTemperature()]
		return [self._programList['oat'].getOutdoorTemperature(),
			self._programList['boiler'].get_input_channel('temperature')]

	def _prepare(self, set_parameter, sensors):
		set_parameter(snc.ProgramType.PROGRAM, snc.ProgramParameterId.TRAINING_ENABLED, 0)
		set_parameter(snc.ProgramType.PROGRAM, snc.ProgramParameterId.MANUAL_MODE_ENABLED, 0)
		set_parameter(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.PRIORITY, self.LOCAL_PRIORITY)
		set_parameter(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.HEAT_EXTRICATION_ENABLED, 0)
		if self.TARGET == 'dhw':
			set_parameter(snc.ProgramType.DHW, snc.DhwParameterId.WORK_MODE, self.MODE_COMFORT)
			set_parameter(snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT, 55)
			set_parameter(snc.ProgramType.DHW, snc.DhwParameterId.SUPPLY_PUMP_OFF_DELAY, 0)
			self.set_sensor_value(sensors[0], 20)
			self.set_sensor_value(sensors[1], 65)
		elif self.TARGET == 'pool':
			set_parameter(snc.ProgramType.POOL, snc.SwimmingPoolParameterId.WORK_MODE, self.MODE_COMFORT)
			set_parameter(snc.ProgramType.POOL, snc.SwimmingPoolParameterId.REQUIRED_POOL_TEMPERATURE, 28)
			self.set_sensor_value(sensors[0], 20)
		elif self.TARGET == 'snow':
			set_parameter(snc.ProgramType.SNOWMELT, snc.SnowMelterParameterId.WORK_MODE, self.MODE_ON)
			minimum = self._read(snc.ProgramType.SNOWMELT, snc.SnowMelterParameterId.MINIMUM_OUTDOOR_TEMPERATURE)
			maximum = self._read(snc.ProgramType.SNOWMELT, snc.SnowMelterParameterId.MAXIMUM_OUTDOOR_TEMPERATURE)
			plate = self._read(snc.ProgramType.SNOWMELT, snc.SnowMelterParameterId.REQUIRED_PLATE_TEMPERATURE)
			frost = self._read(snc.ProgramType.SNOWMELT, snc.SnowMelterParameterId.PRIMARY_CIRCUIT_PROTECTION_TEMPERATURE)
			flow = self._read(snc.ProgramType.SNOWMELT,
				snc.SnowMelterParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE_OF_SECONDARY_CIRCUIT)
			outdoor = math.ceil((minimum + maximum) / 2)
			if not (minimum < outdoor < maximum and -30 <= plate - 5 <= 40
					and -10 <= frost - 2 and frost + 10 <= 100 and -10 <= flow - 8 <= 100):
				raise RuntimeError('Некорректные температурные границы снеготайки')
			self._frost_temperature = frost
			for sensor, value in zip(sensors, (flow - 8, frost + 10, plate - 5, outdoor)):
				self.set_sensor_value(sensor, value)
		else:
			set_parameter(snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.PUMP_MODE, 2)
			set_parameter(snc.ProgramType.HEATING_CIRCUIT,
				snc.HeatingCircuitParameterId.FROST_PROTECTION_TEMPERATURE, 5)
			self.set_sensor_value(sensors[0], self.NORMAL_OUTDOOR)
			self.set_sensor_value(sensors[1], 30)

	def _check_pump(self, channel, threshold=False):
		self._expect('Исходно насос работает', lambda: self._pump_on(channel))
		if threshold:
			boundary = self.LOCAL_PRIORITY + (3 if self.TARGET == 'mixed' else 0)
			self._priority(boundary)
			self._expect('На границе разницы приоритетов насос работает',
				lambda: self._pump_on(channel), hold=self.PUMP_DELAY_MARGIN)
			self._priority()
		# A different generator must not stop a running pump.
		self._priority(self.HIGH_PRIORITY, generator_id=self._generator_id + 1)
		self._expect('Чужой генератор не выключает насос',
			lambda: self._pump_on(channel),
			hold=self.PUMP_DELAY_MARGIN if threshold else self.HOLD_DURATION)
		self._priority()
		self._priority(self.LOCAL_PRIORITY + (4 if self.TARGET == 'mixed' else 1)
			if threshold else self.HIGH_PRIORITY)
		self._expect('Внешний приоритет выключает насос', lambda: self._pump_off(channel),
			self.PUMP_TIMEOUT, hold=self.HOLD_DURATION)
		self._priority()
		self._expect('После PROCEED насос включается', lambda: self._pump_on(channel),
			self.PUMP_TIMEOUT)

	def _check_exception(self, set_parameter, sensors):
		channel = 'primaryPump' if self.TARGET == 'snow' else 'pump'
		self._expect('Исходно насос работает', lambda: self._pump_on(channel))
		self._priority(self.HIGH_PRIORITY)
		self._expect('Контроль: запрос выключает насос', lambda: self._pump_off(channel), self.PUMP_TIMEOUT)
		try:
			set_parameter(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.HEAT_EXTRICATION_ENABLED, 1)
			self._cool(True)
			self._expect('Сброс тепла включает насос вопреки приоритету',
				lambda: self._pump_on(channel), hold=self.HOLD_DURATION)
			self._cool(False)
			self._expect('После сброса тепла приоритет снова действует',
				lambda: self._pump_off(channel), self.PUMP_TIMEOUT)
			if self.TARGET == 'snow':
				self.set_sensor_value(sensors[1], self._frost_temperature - 2)
			else:
				self.set_sensor_value(sensors[0], 0)
			self._expect('Защита от замерзания сохраняет насос загрузки',
				lambda: self._pump_on(channel), hold=self.HOLD_DURATION)
		finally:
			self._cool(False)
			self._priority()

	def _check_pool(self):
		parameter = (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.CURRENT_REQUIRED_POOL_TEMPERATURE)
		self._expect('Бассейн запрашивает ненулевую температуру', lambda: self._read(*parameter) > 0)
		self._priority(self.LOCAL_PRIORITY)
		self._expect('Равный приоритет не выключает бассейн',
			lambda: self._read(*parameter) > 0, hold=self.HOLD_DURATION)
		self._priority()
		self._priority(self.HIGH_PRIORITY, generator_id=self._generator_id + 1)
		self._expect('Другой генератор не выключает бассейн',
			lambda: self._read(*parameter) > 0, hold=self.HOLD_DURATION)
		self._priority()
		self._priority(self.HIGH_PRIORITY)
		self._expect('Внешний приоритет обнуляет уставку бассейна',
			lambda: self._read(*parameter) == 0, hold=self.HOLD_DURATION)
		self._priority()
		self._expect('После PROCEED уставка бассейна восстановлена',
			lambda: self._read(*parameter) > 0)

	def _release(self):
		try:
			if self._cooling:
				self._cool(False)
		finally:
			if self._active_priority is not None:
				self._priority()

	def _run_external_test(self, case):
		self._status = 'FAIL'
		self._active_priority = None
		self._cooling = False
		try:
			self._validate()
			sensors = self._sensors()
			if any(not sensor.is_mapped() for sensor in sensors):
				raise RuntimeError('Не назначен необходимый датчик')
			with preserved_inputs(self, sensors), self._preserved_parameters() as set_parameter:
				try:
					self._prepare(set_parameter, sensors)
					if case in ('pump', 'pump_primary'):
						self._check_pump('supplyPump' if self.TARGET == 'dhw' else
							('primaryPump' if case == 'pump_primary' else 'secondaryPump')
							if self.TARGET == 'snow' else 'pump',
							threshold=self.TARGET in ('mixed', 'direct'))
					elif case == 'exception':
						self._check_exception(set_parameter, sensors)
					else:
						self._check_pool()
					self._status = 'OK'
				finally:
					self._release()
		except Exception as error:
			self._status = 'FAIL'
			print_error(str(error))
		finally:
			# Always release priority and cooling even after cancellation or failed reads.
			try:
				self._release()
			except Exception as error:
				self._status = 'FAIL'
				print_error(f'Не снят внешний запрос: {error}')
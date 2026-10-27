"""Priority request at the strict five-degree snowmelt flow threshold."""

import math

import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter
from consoleLog import print_error, print_log
from scenario.base.consumer_priority import ConsumerPriorityCapture
from scenario.base.snowmelter import SnowmelterScenario
from scenario.steps import ScenarioSteps, preserved_inputs


class SnowmelterPriorityScenario(ConsumerPriorityCapture, SnowmelterScenario):
	MODE_ON = 1
	PRIORITY_THRESHOLD = 5
	PRIORITY_TEST_DEFICIT = 6
	PLATE_MARGIN = 2
	FROST_MARGIN = 5
	DELIVERY_TIMEOUT = 60
	STABILIZATION_DURATION = 5
	# Firmware broadcasts GIVE_WAY every 10 seconds; observe more than two periods.
	NO_REQUEST_DURATION = 25
	REQUEST_TIMEOUT = 45

	def get_default_preset(self):
		return 'snowmelter'

	def force_preset_load(self):
		return True

	def _get_priority_program(self):
		return self._snowmelter

	@staticmethod
	def _is_number(value):
		return isinstance(value, (int, float)) and math.isfinite(value)

	def _read_temperature(self, program_type, parameter_id, index=None):
		parameter = RemoteControlParameter(
			programType=program_type, parameterId=parameter_id,
			programId=self._snowmelter.get_id(), parameterIndex=index,
		)
		if not parameter.read():
			return None
		value = parameter.get_value()
		return value if self._is_number(value) else None

	def _temperatures_match(self, required, flow, inputs, outdoor):
		# Exact comparisons are intentional: rounding tolerance at 5 degrees would
		# allow a temperature on the wrong side of the strict priority threshold.
		if self._read_temperature(snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE) != required:
			return False
		for sensor, expected in [(self._snowmelter.getDirectFlowTemperature(), flow), *inputs]:
			if self._read_temperature(snc.ProgramType.PROGRAM,
					snc.ProgramParameterId.INPUT, sensor.get_id()) != expected:
				return False
		return self._read_temperature(snc.ProgramType.SNOWMELT,
			snc.SnowMelterParameterId.OUTDOOR_TEMPERATURE) == outdoor

	def _run_priority_test(self):
		self._status = 'FAIL'
		original_mode = None
		try:
			original_mode = self._snowmelter.read_parameter_value('workMode')
			if original_mode not in (0, self.MODE_ON):
				raise RuntimeError('Не удалось прочитать режим снеготайки')
			self._run_temperature_cases()
		except Exception as error:
			self._status = 'FAIL'
			print_error(str(error))
		finally:
			try:
				self._end_priority_capture()
			finally:
				if original_mode in (0, self.MODE_ON):
					try:
						if not self._snowmelter.write_parameter('workMode', original_mode):
							raise RuntimeError('Запись режима не подтверждена')
					except Exception as error:
						self._status = 'FAIL'
						print_error(f'Не удалось восстановить режим снеготайки: {error}')

	def _run_temperature_cases(self):
		minimum = self.readMinOutdoorTemperature()
		maximum = self.readMaxOutdoorTemperature()
		required = self.readRequiredFlowTemperature()
		plate = self.readRequiredPlateTemperatureValue()
		protection = self.readFrostProtectionTemperatureValue()
		if any(not self._is_number(value) for value in (minimum, maximum, required, plate, protection)):
			raise RuntimeError('Не прочитаны корректные параметры снеготайки')
		if minimum >= maximum or not 0 < required <= 100:
			raise RuntimeError('Некорректный диапазон температур снеготайки')
		# Whole degrees are exactly representable in protocol temperatures.
		outdoor = math.ceil((minimum + maximum) / 2)
		plate_temperature = math.floor(plate - self.PLATE_MARGIN)
		backward = math.ceil(protection + self.FROST_MARGIN)
		if not (minimum < outdoor < maximum and -30 <= plate_temperature <= 40
				and -10 <= backward <= 100):
			raise RuntimeError('Не удалось выбрать безопасные тестовые температуры')
		if self._outdoor is None:
			raise RuntimeError('Не найдена программа наружной температуры')
		inputs = [(self._snowmelter.getPlateTemperature(), plate_temperature),
			(self._snowmelter.getBackwardFlowTemperature(), backward)]
		direct = self._snowmelter.getDirectFlowTemperature()
		sensors = [direct, *(sensor for sensor, _ in inputs), self._outdoor.getOutdoorTemperature()]
		if any(not sensor.is_mapped() for sensor in sensors):
			raise RuntimeError('Не привязаны необходимые входы снеготайки или улицы')
		steps = ScenarioSteps(self)
		with preserved_inputs(self, sensors):
			for sensor, value in inputs:
				self.set_sensor_value(sensor, value)
			self.setOutdoorTemperature(outdoor)
			flow = required - self.PRIORITY_THRESHOLD
			self.set_sensor_value(direct, flow)
			if not self._snowmelter.write_parameter('workMode', self.MODE_ON):
				raise RuntimeError('Не удалось включить снеготайку')
			boundary_received = lambda: self._temperatures_match(required, flow, inputs, outdoor)
			steps.expect('Подтверждаем активную снеготайку и недогрев ровно 5 °C',
				boundary_received, self.DELIVERY_TIMEOUT, hold=self.STABILIZATION_DURATION)
			self._begin_priority_capture()
			try:
				def no_request_at_boundary():
					return boundary_received() and not self._has_priority_event(snc.ConsumerFunction['GIVE_WAY'])
				steps.expect('При недогреве 5 °C запрос GIVE_WAY отсутствует',
					no_request_at_boundary, self.DELIVERY_TIMEOUT, hold=self.NO_REQUEST_DURATION)
				self._clear_priority_events()
				flow = required - self.PRIORITY_TEST_DEFICIT
				self.set_sensor_value(direct, flow)
				steps.expect('Подтверждаем недогрев 6 °C',
					lambda: self._temperatures_match(required, flow, inputs, outdoor), self.DELIVERY_TIMEOUT)
				if not self._wait_for_message(snc.ConsumerFunction['GIVE_WAY'], self.REQUEST_TIMEOUT):
					raise RuntimeError('Снеготайка не отправила GIVE_WAY при недогреве более 5 °C')
				if not self._temperatures_match(required, flow, inputs, outdoor):
					raise RuntimeError('Условия недогрева изменились во время ожидания GIVE_WAY')
			finally:
				self._end_priority_capture()
		self._status = 'OK'
		print_log('Порог 5 °C и включение запроса приоритета снеготайки проверены')
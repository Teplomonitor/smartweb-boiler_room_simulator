import math
import time

import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter

from consoleLog import print_error, print_log
from scenario.base.consumer_priority import ConsumerPriorityCapture
from scenario.base.dhw import DhwScenario
from scenario.steps import preserved_inputs


class DhwPriorityScenario(ConsumerPriorityCapture, DhwScenario):
	DHW_COLD_TEMPERATURE = 20
	DHW_COMFORT_TEMPERATURE = 55
	FLOW_RATE = 100
	REQUEST_TIMEOUT = 45
	PARAMETER_TIMEOUT = 60
	COLD_FAULT_DELAY = 60 * 60
	COLD_FAULT_TOLERANCE = 2 * 60
	NO_REQUEST_HOLD = 15
	GENERATOR_TEMPERATURE = 70
	FLOW_THROUGH_GENERATOR_TEMPERATURE = 35

	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		self._generator = self._find_generator()

	def get_default_preset(self):
		return 'boiler_3_5_2'

	def force_preset_load(self):
		return True

	def _find_generator(self):
		generator_id = self._dhw.get_temperature_source()
		for program in self.get_program_list():
			if program.get_id() == generator_id and program.get_type() == snc.ProgramType.BOILER:
				return program
		return None

	def _get_priority_program(self):
		return self._dhw

	def _read_consumer_temperature(self, parameter_id):
		parameter = RemoteControlParameter(
			programType=snc.ProgramType.CONSUMER,
			parameterId=parameter_id,
			programId=self._dhw.get_id(),
		)
		if not parameter.read():
			return None
		value = parameter.get_value()
		if not isinstance(value, (int, float)) or not math.isfinite(value):
			return None
		return value

	def _required_and_generator_temperatures_match(self, flow_through):
		required = self._read_consumer_temperature(snc.ConsumerParameterId.REQUIRED_TEMPERATURE)
		generator = self._read_consumer_temperature(snc.ConsumerParameterId.GENERATOR_TEMPERATURE)
		if required is None or generator is None:
			return False
		if flow_through:
			return required > generator
		return required > 0 and generator > required

	def _wait_for_temperature_condition(self, flow_through):
		return self.wait_event(
			lambda: self._required_and_generator_temperatures_match(flow_through),
			self.PARAMETER_TIMEOUT,
		)

	def _get_test_sensors(self, flow_through):
		if self._generator is None:
			raise RuntimeError('Не найдена программа-котёл, заданная источником ГВС')
		sensors = [self._dhw.get_temperature(), self._generator.get_temperature()]
		if flow_through:
			sensors.append(self._dhw.get_input_channel('flow'))
		if any(not sensor.is_mapped() for sensor in sensors):
			raise RuntimeError('Не привязаны необходимые входы ГВС или котла')
		if flow_through and not self._dhw.get_output_channel('analogLoadingPump').is_mapped():
			raise RuntimeError('Не привязан аналоговый насос загрузки для проточной схемы')
		return sensors

	def _activate_dhw_heating(self):
		if not self._dhw.write_parameter('temperatureComfort', self.DHW_COMFORT_TEMPERATURE):
			raise RuntimeError('Не удалось задать комфортную температуру ГВС')
		if not self._dhw.write_parameter('workMode', self.MODE_COMFORT):
			raise RuntimeError('Не удалось включить режим комфорта ГВС')

	def _set_priority_test_inputs(self, flow_through):
		self.set_sensor_value(self._dhw.get_temperature(), self.DHW_COLD_TEMPERATURE)
		generator_temperature = (self.FLOW_THROUGH_GENERATOR_TEMPERATURE if flow_through
			else self.GENERATOR_TEMPERATURE)
		self.set_sensor_value(self._generator.get_temperature(), generator_temperature)
		if flow_through:
			self.set_sensor_value(self._dhw.get_input_channel('flow'), self.FLOW_RATE)

	def _assert_no_give_way_after_proceed(self):
		proceed_index = self._priority_event_index(snc.ConsumerFunction['PROCEED'])
		if proceed_index is None:
			raise RuntimeError('Не получено сообщение PROCEED от ГВС')
			
		deadline = time.monotonic() + self.NO_REQUEST_HOLD
		while time.monotonic() < deadline:
			with self._priority_lock:
				if any(event[1] == snc.ConsumerFunction['GIVE_WAY']
						for event in self._priority_events[proceed_index + 1:]):
					raise RuntimeError('ГВС продолжила отправлять GIVE_WAY после PROCEED')
			if self.wait(1) is False:
				raise RuntimeError('Ожидание сценария прервано')

	def _run_priority_test(self, flow_through=False, verify_cold_suppression=False):
		self._status = 'FAIL'
		original_mode = self._dhw.read_parameter_value('workMode')
		original_comfort = self._dhw.read_parameter_value('temperatureComfort')
		if original_mode is None or original_comfort is None:
			print_error('Не удалось прочитать параметры режима и температуры ГВС')
			return

		try:
			sensors = self._get_test_sensors(flow_through)
			with preserved_inputs(self, sensors):
				self._begin_priority_capture()
				try:
					self._set_priority_test_inputs(flow_through)
					self._activate_dhw_heating()
					if not self._wait_for_temperature_condition(flow_through):
						raise RuntimeError('Не подтверждены требуемые температуры ГВС и котла')
					if not self._wait_for_message(snc.ConsumerFunction['GIVE_WAY'], self.REQUEST_TIMEOUT):
						raise RuntimeError('ГВС не отправила сообщение GIVE_WAY')

					if verify_cold_suppression:
						print_log('Ждём выявления длительного недогрева ГВС (до 60 минут)')
						if not self._wait_for_message(
							snc.ConsumerFunction['PROCEED'],
							self.COLD_FAULT_DELAY + self.COLD_FAULT_TOLERANCE,
						):
							raise RuntimeError('ГВС не сняла запрос приоритета после длительного недогрева')
						if not self._required_and_generator_temperatures_match(False):
							raise RuntimeError('Перед проверкой запрета не подтверждены горячий источник и недогрев ГВС')
						self._assert_no_give_way_after_proceed()
						self._status = 'OK'
					else:
						self._status = 'OK'
				finally:
					self._end_priority_capture()
		except Exception as error:
			print_error(str(error))
		finally:
			for parameter, value, error_message in (
				('workMode', original_mode, 'Не удалось восстановить режим ГВС'),
				('temperatureComfort', original_comfort,
				 'Не удалось восстановить комфортную температуру ГВС'),
			):
				try:
					if not self._dhw.write_parameter(parameter, value):
						raise RuntimeError(error_message)
				except Exception as error:
					print_error(f'{error_message}: {error}')
					self._status = 'FAIL'

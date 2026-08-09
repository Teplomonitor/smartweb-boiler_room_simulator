from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc
import smartnet.remoteControl as sr


class Scenario(DistrictHeatingScenario):
	LOW_REQUEST_TEMPERATURE = 40
	HIGH_REQUEST_TEMPERATURE = 65
	MIN_VALVE_MOVEMENT = 5
	VALVE_RUNNING_TIME = 30
	VALVE_RESPONSE_TIMEOUT = 3 * 60
	STABILIZATION_DURATION = 30
	FLOW_CONTROL_DURATION = 10 * 60
	FLOW_CONTROL_TIMEOUT = 30 * 60
	MAXIMUM_TEMPERATURE_ERROR = 3

	def get_scenario_title(self):
		return 'District Heating: maximum consumer request controls valve'

	def get_scenario_description(self):
		return (
			'ИТП выбирает максимальную требуемую температуру подачи от отопительных '
			'контуров и ГВС, изменяет положение крана и удерживает температуру подачи '
			'в дом с расхождением не более 3 градусов в среднем за 10 минут'
		)

	def get_checklist_id(self):
		return '3.12.6'

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'outdoor': snc.ProgramType.OUTDOOR_SENSOR,
			'heatingCircuit1': snc.ProgramType.HEATING_CIRCUIT,
			'heatingCircuit2': snc.ProgramType.HEATING_CIRCUIT,
			'dhw': snc.ProgramType.DHW,
		}

	def read_consumer_request(self, program):
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.CONSUMER,
			parameterId=snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
			programId=program.get_id(),
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def write_consumer_request(self, program, value):
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.CONSUMER,
			parameterId=snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
			parameterValue=value,
			programId=program.get_id(),
		)
		if not parameter.write():
			return None
		return value

	def read_required_temperature(self):
		source_id = self.read_temperature_source_id()
		if source_id is None:
			return None

		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.TEMPERATURE_SOURCE,
			parameterId=snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE,
			programId=source_id,
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def read_temperature_source_id(self):
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.DISTRICT_HEATING,
			parameterId=snc.DistrictHeatingParameterId.PARAM_TEMPERATURE_SOURCE_ID,
			programId=self._district_heating.get_id(),
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def run(self):
		heating_circuit_1 = self._programList['heatingCircuit1']
		heating_circuit_2 = self._programList['heatingCircuit2']
		dhw = self._programList['dhw']
		analog_valve = self._district_heating.get_output_channel('analog_valve')
		direct_temperature = self._district_heating.get_input_channel('direct_temp')

		if not analog_valve.is_mapped():
			print_error('Не найден аналоговый выход крана ИТП')
			self._status = 'FAIL'
			return
		if not direct_temperature.is_mapped():
			print_error('Не найден датчик подачи в дом ИТП')
			self._status = 'FAIL'
			return

		source_id = self.read_temperature_source_id()
		if source_id is None:
			print_error('Не удалось получить ID температурного источника ИТП')
			self._status = 'FAIL'
			return

		consumer_programs = (heating_circuit_1, heating_circuit_2, dhw)
		original_requests = []
		for program in consumer_programs:
			request = self.read_consumer_request(program)
			if request is None:
				print_error(
					f'Не удалось получить требуемую температуру программы {program.get_id()}'
				)
				self._status = 'FAIL'
				return
			original_requests.append(request)

		original_valve_running_time = self.read_valve_running_time()
		initial_valve = analog_valve.get_value()
		if original_valve_running_time is None or initial_valve is None:
			print_error('Не удалось получить исходные параметры крана ИТП')
			self._status = 'FAIL'
			return

		try:
			if self.write_valve_running_time(self.VALVE_RUNNING_TIME) is None:
				print_error('Не удалось изменить время хода крана ИТП')
				self._status = 'FAIL'
				return

			for program in consumer_programs:
				if self.write_consumer_request(program, self.LOW_REQUEST_TEMPERATURE) is None:
					print_error('Не удалось установить исходные запросы потребителей')
					self._status = 'FAIL'
					return
			self.wait(self.STABILIZATION_DURATION)
			low_required_temperature = self.read_required_temperature()
			low_valve = analog_valve.get_value()
			if low_required_temperature is None or low_valve is None:
				print_error('Не удалось получить состояние ИТП после минимального запроса')
				self._status = 'FAIL'
				return

			if low_required_temperature != self.LOW_REQUEST_TEMPERATURE:
				print_error(
					f'ИТП выбрал неверную максимальную уставку: '
					f'{low_required_temperature} вместо {self.LOW_REQUEST_TEMPERATURE}'
				)
				self._status = 'FAIL'
				return

			if self.write_consumer_request(heating_circuit_2, self.HIGH_REQUEST_TEMPERATURE) is None:
				print_error('Не удалось установить повышенный запрос отопительного контура')
				self._status = 'FAIL'
				return

			self.wait(self.STABILIZATION_DURATION)
			required_temperature = self.read_required_temperature()
			final_valve = analog_valve.get_value()
			if required_temperature is None or final_valve is None:
				print_error('Не удалось получить состояние ИТП после повышенного запроса')
				self._status = 'FAIL'
				return

			maximum_request = max(
				self.LOW_REQUEST_TEMPERATURE,
				self.HIGH_REQUEST_TEMPERATURE,
			)
			print_log(
				f'Требуемая температура источника: {required_temperature:.1f} C, '
				f'максимальный запрос: {maximum_request:.1f} C'
			)
			if abs(required_temperature - maximum_request) > 0.1:
				print_error('ИТП не выбрал максимальный запрос потребителей')
				self._status = 'FAIL'
				return

			movement = final_valve - low_valve
			print_log(
				f'Положение крана: после минимального запроса {low_valve}, '
				f'после повышенного запроса {final_valve}, изменение {movement}'
			)
			if movement < self.MIN_VALVE_MOVEMENT:
				print_error('Положение крана не изменилось в сторону открытия')
				self._status = 'FAIL'
				return

			print_log(
				f'Проверяем поддержание температуры подачи в дом в течение '
				f'{self.FLOW_CONTROL_DURATION} секунд'
			)
			result = self.wait_value_maintaining(
				direct_temperature.get_value,
				lambda: required_temperature,
				self.FLOW_CONTROL_DURATION,
				self.FLOW_CONTROL_TIMEOUT,
				dtAvrMax=self.MAXIMUM_TEMPERATURE_ERROR,
			)
			if result:
				self._status = 'OK'
			else:
				self._status = 'FAIL'
		finally:
			if self.write_valve_running_time(original_valve_running_time) is None:
				print_error('Не удалось восстановить исходное время хода крана')
				self._status = 'FAIL'
			for program, request in zip(consumer_programs, original_requests):
				if self.write_consumer_request(program, request) is None:
					print_error(
						f'Не удалось восстановить запрос программы {program.get_id()}'
					)
					self._status = 'FAIL'
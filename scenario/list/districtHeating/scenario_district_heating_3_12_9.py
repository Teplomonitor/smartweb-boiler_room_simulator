from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc
import smartnet.remoteControl as sr
import smartnet.units as snu


class Scenario(DistrictHeatingScenario):
	OUTDOOR_TEMPERATURE_MARGIN = 5
	OUTDOOR_TEMPERATURE_TOLERANCE = 1
	OUTDOOR_TEMPERATURE_TIMEOUT = 6 * 60
	REQUEST_ON_STABILIZATION_DURATION = 20
	REQUEST_ON_TIMEOUT = 3 * 60
	REQUEST_OFF_TIMEOUT = 3 * 60
	PUMP_OFF_DELAY = 5 * 60
	PUMP_OFF_EARLY_MARGIN = 30
	PUMP_OFF_TIMEOUT = 2 * 60
	PUMP_OFF_STABILIZATION_DURATION = 20

	def get_scenario_title(self):
		return 'District Heating: circulation pump switches off without heat request'

	def get_scenario_description(self):
		return (
			'Если у потребителя нет запроса на тепло (уставка равна 0 или SENSOR_UNDEFINED), '
			'насос циркуляции ИТП выключается с задержкой пять минут'
		)

	def get_checklist_id(self):
		return '3.12.9'

	def get_default_preset(self):
		return 'district_heating_3_12_8'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'outdoor': snc.ProgramType.OUTDOOR_SENSOR,
			'heatingCircuit': snc.ProgramType.HEATING_CIRCUIT,
		}

	def read_parameter(self, program_type, parameter_id):
		parameter = sr.RemoteControlParameter(
			programType=program_type,
			parameterId=parameter_id,
			programId=self._heating_circuit.get_id(),
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def read_heating_circuit_parameter(self, parameter_id):
		return self.read_parameter(snc.ProgramType.HEATING_CIRCUIT, parameter_id)

	def read_circuit_outdoor_temperature(self):
		return self.read_parameter(
			snc.ProgramType.CIRCUIT,
			snc.CircuitParameterId.OUTDOOR_TEMPERATURE,
		)

	def circuit_outdoor_temperature_is_close(self, target_temperature):
		outdoor_temperature = self.read_circuit_outdoor_temperature()
		return (
			outdoor_temperature is not None
			and abs(outdoor_temperature - target_temperature) <= self.OUTDOOR_TEMPERATURE_TOLERANCE
		)

	def wait_circuit_outdoor_temperature(self, target_temperature):
		return self.wait_event(
			lambda: self.circuit_outdoor_temperature_is_close(target_temperature),
			self.OUTDOOR_TEMPERATURE_TIMEOUT,
		)

	def read_consumer_required_temperature(self):
		return self.read_parameter(
			snc.ProgramType.CONSUMER,
			snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
		)

	def is_no_heat_request(self, required_temperature):
		return required_temperature in (0, snu.SENSOR_UNDEFINED, 'OPEN')

	def has_heat_request(self, required_temperature):
		return (
			required_temperature is not None
			and not self.is_no_heat_request(required_temperature)
		)

	def run(self):
		self._heating_circuit = self._programList['heatingCircuit']
		outdoor_sensor = self._outdoor.getOutdoorTemperature()
		circulation_pump = self._district_heating.get_output_channel('circulation_pump')

		if not outdoor_sensor.is_mapped():
			print_error('Не найден датчик уличной температуры')
			self._status = 'FAIL'
			return

		if not circulation_pump.is_mapped():
			print_error('Не найден выход циркуляционного насоса')
			self._status = 'FAIL'
			return

		initial_outdoor_temperature = outdoor_sensor.get_value()
		pump_state = circulation_pump.get_value()
		pump_off_temperature = self.read_heating_circuit_parameter(
			snc.HeatingCircuitParameterId.PUMP_OFF_OUTDOOR_TEMPERATURE,
		)
		initial_required_temperature = self.read_consumer_required_temperature()

		if initial_outdoor_temperature is None:
			print_error('Не удалось получить исходную уличную температуру')
			self._status = 'FAIL'
			return

		if pump_state is None:
			print_error('Не удалось получить исходное состояние насоса циркуляции')
			self._status = 'FAIL'
			return

		if pump_off_temperature is None:
			print_error('Не удалось получить температуру отключения насоса отопительного контура')
			self._status = 'FAIL'
			return

		if initial_required_temperature is None:
			print_error('Не удалось получить исходную уставку потребителя')
			self._status = 'FAIL'
			return

		cold_outdoor_temperature = pump_off_temperature - self.OUTDOOR_TEMPERATURE_MARGIN
		hot_outdoor_temperature = pump_off_temperature + self.OUTDOOR_TEMPERATURE_MARGIN

		try:
			print_log(
				f'Делаем на улице холодно ({cold_outdoor_temperature:.1f} C), '
				'чтобы потребитель запросил тепло'
			)
			self.set_sensor_value(outdoor_sensor, cold_outdoor_temperature)

			print_log(
				f'Ждём, пока отопительный контур увидит температуру около '
				f'{cold_outdoor_temperature:.1f} C, не более '
				f'{self.OUTDOOR_TEMPERATURE_TIMEOUT} секунд'
			)
			if not self.wait_circuit_outdoor_temperature(cold_outdoor_temperature):
				print_error('Отопительный контур не увидел заданную холодную уличную температуру')
				self._status = 'FAIL'
				return

			print_log(
				f'Ждём включения насоса и наличия запроса тепла не более '
				f'{self.REQUEST_ON_TIMEOUT} секунд'
			)
			if not self.wait_state_permanence(
				lambda: (
					circulation_pump.get_value() == self.RELAY_ON
					and self.has_heat_request(self.read_consumer_required_temperature())
				),
				self.REQUEST_ON_STABILIZATION_DURATION,
				self.REQUEST_ON_TIMEOUT,
			):
				print_error('Потребитель не запросил тепло или насос не включился')
				self._status = 'FAIL'
				return

			print_log(
				f'Делаем на улице жарко ({hot_outdoor_temperature:.1f} C), '
				'чтобы потребитель прекратил запрос тепла'
			)
			self.set_sensor_value(outdoor_sensor, hot_outdoor_temperature)

			print_log(
				f'Ждём, пока отопительный контур увидит температуру около '
				f'{hot_outdoor_temperature:.1f} C, не более '
				f'{self.OUTDOOR_TEMPERATURE_TIMEOUT} секунд'
			)
			if not self.wait_circuit_outdoor_temperature(hot_outdoor_temperature):
				print_error('Отопительный контур не увидел заданную горячую уличную температуру')
				self._status = 'FAIL'
				return

			print_log(
				f'Ждём уставку 0 или SENSOR_UNDEFINED не более '
				f'{self.REQUEST_OFF_TIMEOUT} секунд'
			)
			if not self.wait_event(
				lambda: self.is_no_heat_request(self.read_consumer_required_temperature()),
				self.REQUEST_OFF_TIMEOUT,
			):
				print_error('Потребитель не прекратил запрос тепла')
				self._status = 'FAIL'
				return

			early_off_check_duration = self.PUMP_OFF_DELAY - self.PUMP_OFF_EARLY_MARGIN
			print_log(
				f'Проверяем, что насос остаётся включённым первые '
				f'{early_off_check_duration} секунд задержки'
			)
			if not self.wait_state_permanence(
				lambda: circulation_pump.get_value() == self.RELAY_ON,
				early_off_check_duration,
			):
				print_error('Насос выключился раньше задержки пять минут')
				self._status = 'FAIL'
				return

			print_log(
				f'Ждём выключения насоса после задержки пять минут не более '
				f'{self.PUMP_OFF_TIMEOUT} секунд'
			)
			if not self.wait_state_permanence(
				lambda: circulation_pump.get_value() == self.RELAY_OFF,
				self.PUMP_OFF_STABILIZATION_DURATION,
				self.PUMP_OFF_TIMEOUT,
			):
				print_error('Насос циркуляции не выключился после отсутствия запроса тепла')
				self._status = 'FAIL'
				return

			print_log('Проверка задержки выключения насоса циркуляции пройдена')
			self._status = 'OK'
		finally:
			self.set_sensor_value(outdoor_sensor, initial_outdoor_temperature)

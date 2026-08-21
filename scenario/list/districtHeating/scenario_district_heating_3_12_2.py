from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.message as snm
import smartnet.constants as snc
from smartnet.remoteControl import bytesToTemp


class Scenario(DistrictHeatingScenario):
	OUTDOOR_TEMPERATURE_POINT_I = 10
	OUTDOOR_TEMPERATURE_OFFSET = 5
	OUTDOOR_TEMPERATURE_FILTER_WAIT = 30
	BACKWARD_TEMPERATURE_RECALCULATION_WAIT = 10
	OUTDOOR_TEMPERATURE_MESSAGE_TIMEOUT = 30

	def get_scenario_title(self):
		return 'District Heating: outdoor-temperature backward limit'

	def get_scenario_description(self):
		return 'Если Темп. огранич. = Авто, максимально допустимая температура обратки зависит от уличной температуры по двум заданным точкам'

	def get_checklist_id(self):
		return '3.12.2'

	def read_filtered_outdoor_temperature(self, requested_temperature):
		self.set_outdoor_temperature(requested_temperature)

		print_log(
			'Подождём, пока программа улицы отфильтрует температуру '
			f'{requested_temperature:.1f} °C'
		)
		self.wait(self.OUTDOOR_TEMPERATURE_FILTER_WAIT)

		msg = snm.Message()
		result = msg.recv(
			snm.Message(
				snc.ProgramType.OUTDOOR_SENSOR, None,
				snc.OutdoorSensorFunction.GET_TEMPERATURE,
				snc.RequestFlag.RESPONSE),
			self.OUTDOOR_TEMPERATURE_MESSAGE_TIMEOUT
		)

		if not result:
			return None

		data = result.get_data()
		if data is None or len(data) < 2:
			return None

		return bytesToTemp(data[0:2])

	def run(self):
		print_log('Задаём режим авто.')
		self.write_backward_control_type(self.BACKWARD_CONTROL_TYPE_AUTO)
		
		control_type = self.read_backward_control_type()
		if control_type is None:
			print_error('Не удалось получить параметр Темп. огранич.')
			self._status = 'FAIL'
			return

		if control_type != self.BACKWARD_CONTROL_TYPE_AUTO:
			print_error(f'Ожидался режим Авто (1), получено: {control_type}')
			self._status = 'FAIL'
			return

		maximum_temperature_i = self.read_maximum_backward_temperature()
		maximum_temperature_ii = self.read_maximum_backward_temperature_ii()
		outdoor_temperature_ii = self.read_outdoor_temperature_ii()
		if (
			maximum_temperature_i is None
			or maximum_temperature_ii is None
			or outdoor_temperature_ii is None
		):
			print_error('Не удалось получить параметры точек ограничения температуры обратки')
			self._status = 'FAIL'
			return

		outdoor_temperature_i = self.OUTDOOR_TEMPERATURE_POINT_I
		if outdoor_temperature_ii == outdoor_temperature_i:
			print_error('Точки зависимости имеют одинаковую уличную температуру')
			self._status = 'FAIL'
			return

		if outdoor_temperature_ii > outdoor_temperature_i:
			print_error(
				'Вторая точка зависимости должна быть ниже первой, '
				f'получено: {outdoor_temperature_ii:.1f} °C'
			)
			self._status = 'FAIL'
			return

		point_distance = outdoor_temperature_i - outdoor_temperature_ii
		test_outdoor_temperatures = [
			outdoor_temperature_ii - self.OUTDOOR_TEMPERATURE_OFFSET,
			outdoor_temperature_ii,
			outdoor_temperature_ii + point_distance / 4,
			outdoor_temperature_ii + point_distance / 2,
			outdoor_temperature_ii + point_distance * 3 / 4,
			outdoor_temperature_i,
			outdoor_temperature_i + self.OUTDOOR_TEMPERATURE_OFFSET,
		]

		for test_outdoor_temperature in test_outdoor_temperatures:
			actual_outdoor_temperature = self.read_filtered_outdoor_temperature(
				test_outdoor_temperature
			)
			if actual_outdoor_temperature is None:
				print_error(
					'Не удалось получить усреднённую уличную температуру '
					f'для заданного значения {test_outdoor_temperature:.1f} °C'
				)
				self._status = 'FAIL'
				return

			print_log(
				'Подождём, пока программа ИТП пересчитает температуру обратки '
				'в соответствии с новой уличной температурой'
			)
			self.wait(self.BACKWARD_TEMPERATURE_RECALCULATION_WAIT)

			current_maximum_temperature = self.read_current_maximum_backward_temperature()
			if current_maximum_temperature is None:
				print_error('Не удалось получить текущий предел обратки')
				self._status = 'FAIL'
				return

			if actual_outdoor_temperature > outdoor_temperature_i:
				expected_temperature = maximum_temperature_i
			elif actual_outdoor_temperature < outdoor_temperature_ii:
				expected_temperature = maximum_temperature_ii
			else:
				expected_temperature = maximum_temperature_i + (
					(actual_outdoor_temperature - outdoor_temperature_i)
					* (maximum_temperature_ii - maximum_temperature_i)
					/ (outdoor_temperature_ii - outdoor_temperature_i)
				)

			difference = abs(current_maximum_temperature - expected_temperature)
			print_log(
				f'Т улицы: {actual_outdoor_temperature:.1f} °C, '
				f'ожидаемый предел: {expected_temperature:.1f} K, '
				f'текущий предел: {current_maximum_temperature:.1f} K, '
				f'расхождение: {difference:.1f} K'
			)

			if difference > self.BACKWARD_TEMPERATURE_TOLERANCE:
				print_error(
					'Текущий предел обратки отличается от ожидаемого значения '
					f'больше чем на {self.BACKWARD_TEMPERATURE_TOLERANCE} K'
				)
				self._status = 'FAIL'
				return

		print_log(
			'Проверка автоматического ограничения температуры обратки '
			'в диапазоне и за его пределами пройдена'
		)
		self._status = 'OK'

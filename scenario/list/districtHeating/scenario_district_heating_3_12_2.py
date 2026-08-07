from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario


class Scenario(DistrictHeatingScenario):
	OUTDOOR_TEMPERATURE_POINT_I = 10

	def get_scenario_title(self):
		return 'District Heating: outdoor-temperature backward limit'

	def get_scenario_description(self):
		return 'Если Темп. огранич. = Авто, максимально допустимая температура обратки зависит от уличной температуры по двум заданным точкам'

	def get_checklist_id(self):
		return '3.12.2'

	def run(self):
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

		test_outdoor_temperature = (outdoor_temperature_i + outdoor_temperature_ii) / 2
		self.set_outdoor_temperature(test_outdoor_temperature)
		self.wait(2)

		actual_outdoor_temperature = self.get_outdoor_temperature()
		current_maximum_temperature = self.read_current_maximum_backward_temperature()
		if actual_outdoor_temperature is None or current_maximum_temperature is None:
			print_error('Не удалось получить текущую уличную температуру или предел обратки')
			self._status = 'FAIL'
			return

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
				'Текущий предел обратки отличается от линейной зависимости '
				f'больше чем на {self.BACKWARD_TEMPERATURE_TOLERANCE} K'
			)
			self._status = 'FAIL'
			return

		print_log('Проверка автоматического ограничения температуры обратки пройдена')
		self._status = 'OK'

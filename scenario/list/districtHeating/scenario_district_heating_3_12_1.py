from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario


class Scenario(DistrictHeatingScenario):
	def get_scenario_title(self):
		return 'District Heating: constant maximum backward temperature'

	def get_scenario_description(self):
		return 'Если Темп. огранич. = Фикс., максимально допустимая температура обратки в город равна Макс. Т обратки I'

	def get_checklist_id(self):
		return '3.12.1'

	def run(self):
		print_log('Задаём режим фикс.')
		self.write_backward_control_type(self.BACKWARD_CONTROL_TYPE_CONST)
		
		control_type = self.read_backward_control_type()
		if control_type is None:
			print_error('Не удалось получить параметр Темп. огранич.')
			self._status = 'FAIL'
			return

		if control_type != self.BACKWARD_CONTROL_TYPE_CONST:
			print_error(f'Ожидался режим Фикс. (0), получено: {control_type}')
			self._status = 'FAIL'
			return

		maximum_temperature = self.read_maximum_backward_temperature()
		if maximum_temperature is None:
			print_error('Не удалось получить параметр Макс. Т обратки I')
			self._status = 'FAIL'
			return

		print_log('Ждём, пока программа ИТП пересчитает порог температуры обратки')
		self.wait(20)
		
		current_maximum_temperature = self.read_current_maximum_backward_temperature()
		if current_maximum_temperature is None:
			print_error('Не удалось получить текущую максимально допустимую температуру обратки')
			self._status = 'FAIL'
			return

		difference = abs(current_maximum_temperature - maximum_temperature)
		print_log(
			f'Макс. Т обратки I: {maximum_temperature:.1f} K, '
			f'текущий предел: {current_maximum_temperature:.1f} K, '
			f'расхождение: {difference:.1f} K'
		)

		if difference > self.BACKWARD_TEMPERATURE_TOLERANCE:
			print_error(
				'Текущая максимально допустимая температура обратки '
				f'отличается больше чем на {self.BACKWARD_TEMPERATURE_TOLERANCE} K'
			)
			self._status = 'FAIL'
			return

		print_log('Проверка постоянного ограничения температуры обратки пройдена')
		self._status = 'OK'

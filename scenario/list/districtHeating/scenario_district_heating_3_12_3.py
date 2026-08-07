from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario


class Scenario(DistrictHeatingScenario):
	OVER_TEMPERATURE_MARGIN = 5
	OVER_TEMPERATURE_DURATION = 60
	MIN_VALVE_MOVEMENT = 1

	def get_scenario_title(self):
		return 'District Heating: valve closes on high city return temperature'

	def get_scenario_description(self):
		return 'Если температура обратки в город выше допустимого значения в течение минуты, кран закрывается'

	def get_checklist_id(self):
		return '3.12.3'

	def run(self):
		maximum_temperature = self.read_current_maximum_backward_temperature()
		if maximum_temperature is None:
			print_error('Не удалось получить текущую максимально допустимую температуру обратки')
			self._status = 'FAIL'
			return

		test_temperature = maximum_temperature + self.OVER_TEMPERATURE_MARGIN
		city_return_sensor = self._district_heating.get_input_channel('supply_backward_temp')
		if not city_return_sensor.is_mapped():
			print_error('Не найден датчик температуры обратки в город')
			self._status = 'FAIL'
			return

		if test_temperature > city_return_sensor.getMax():
			print_error(
				f'Невозможно установить температуру обратки выше предела: '
				f'{maximum_temperature:.1f} K'
			)
			self._status = 'FAIL'
			return

		analog_valve = self._district_heating.get_output_channel('analog_valve')
		if not analog_valve.is_mapped():
			print_error('Не найден аналоговый выход крана')
			self._status = 'FAIL'
			return

		initial_valve = analog_valve.get_value()
		if initial_valve is None:
			print_error('Не удалось получить начальное положение крана')
			self._status = 'FAIL'
			return

		if initial_valve <= self.MIN_VALVE_MOVEMENT:
			print_error(
				f'Кран уже закрыт (значение {initial_valve}), '
				'невозможно проверить его закрытие'
			)
			self._status = 'FAIL'
			return

		print_log(
			f'Устанавливаем температуру обратки в город {test_temperature:.1f} K '
			f'(предел {maximum_temperature:.1f} K)'
		)
		self.set_sensor_value(city_return_sensor, test_temperature)

		print_log(
			f'Ждём {self.OVER_TEMPERATURE_DURATION} секунд, чтобы проверить закрытие крана'
		)
		self.wait(self.OVER_TEMPERATURE_DURATION)

		final_valve = analog_valve.get_value()
		if final_valve is None:
			print_error('Не удалось получить положение крана после проверки')
			self._status = 'FAIL'
			return

		movement = initial_valve - final_valve
		print_log(
			f'Положение крана: до проверки {initial_valve}, '
			f'после проверки {final_valve}, изменение {movement}'
		)

		if movement < self.MIN_VALVE_MOVEMENT:
			print_error(
				'Кран не начал закрываться в течение '
			f'{self.OVER_TEMPERATURE_DURATION} секунд'
			)
			self._status = 'FAIL'
			return

		print_log('Проверка закрытия крана при высокой температуре обратки пройдена')
		self._status = 'OK'

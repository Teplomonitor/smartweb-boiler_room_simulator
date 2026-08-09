from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario


class Scenario(DistrictHeatingScenario):
	OVER_TEMPERATURE_MARGIN = 5
	OVER_TEMPERATURE_DURATION = 60
	MIN_VALVE_MOVEMENT = 10
	MIN_VALVE_MOVEMENT_DURATION = 30
	MIN_VALVE_POSITION = 10
	VALVE_SLOW_CLOSING_DURATION = MIN_VALVE_MOVEMENT_DURATION*10

	def get_scenario_title(self):
		return 'District Heating: high house return blocks valve closing'

	def get_scenario_description(self):
		return 'Если обратка из дома выше допустимого значения, высокая обратка в город не должна закрывать кран'

	def get_checklist_id(self):
		return '3.12.4'

	def run(self):
		maximum_temperature = self.read_current_maximum_backward_temperature()
		if maximum_temperature is None:
			print_error('Не удалось получить текущую максимально допустимую температуру обратки')
			self._status = 'FAIL'
			return

		city_return_sensor = self._district_heating.get_input_channel('supply_backward_temp')
		house_return_sensor = self._district_heating.get_input_channel('backward_temp')
		if not city_return_sensor.is_mapped():
			print_error('Не найден датчик температуры обратки в город')
			self._status = 'FAIL'
			return

		if not house_return_sensor.is_mapped():
			print_error('Не найден датчик температуры обратки из дома')
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

		if initial_valve <= self.MIN_VALVE_POSITION:
			print_error(
				f'Кран уже закрыт (значение {initial_valve}), '
				'невозможно проверить отсутствие закрытия'
			)
			self._status = 'FAIL'
			return

		original_valve_running_time = self.read_valve_running_time()
		if original_valve_running_time is None:
			print_error('Не удалось получить исходное время хода крана')
			self._status = 'FAIL'
			return

		try:
			print_log(
				f'Сделаем время работы крана {self.MIN_VALVE_MOVEMENT_DURATION} секунд, чтобы пройти тест быстрее'
			)
			self.write_valve_running_time(self.MIN_VALVE_MOVEMENT_DURATION)

			city_test_temperature = maximum_temperature + self.OVER_TEMPERATURE_MARGIN
			house_test_temperature = maximum_temperature + self.OVER_TEMPERATURE_MARGIN
			print_log(
				f'Устанавливаем температуру обратки в город {city_test_temperature:.1f} C '
				f'(предел {maximum_temperature:.1f} K)'
			)
			self.set_sensor_value(city_return_sensor, city_test_temperature)

			print_log(
				f'Устанавливаем высокую температуру обратки из дома '
				f'{house_test_temperature:.1f} C, чтобы имитировать высокотемпературного потребителя'
			)
			self.set_sensor_value(house_return_sensor, house_test_temperature)

			print_log(
				f'Ждём {self.OVER_TEMPERATURE_DURATION} секунд для обработки высокой обратки'
			)
			if not self.wait(self.OVER_TEMPERATURE_DURATION):
				self._status = 'FAIL'
				return

			print_log(
				'Кран не должен закрываться из-за высокой обратки в город, '
				f'проверим положение через {self.VALVE_SLOW_CLOSING_DURATION} секунд'
			)
			if not self.wait(self.VALVE_SLOW_CLOSING_DURATION):
				self._status = 'FAIL'
				return

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

			if movement >= self.MIN_VALVE_MOVEMENT:
				print_error(
					'Кран начал закрываться при наличии высокотемпературного потребителя: '
					f'изменение положения {movement} >= {self.MIN_VALVE_MOVEMENT}'
				)
				self._status = 'FAIL'
				return

			print_log(
				'Проверка блокировки закрытия крана при высокой обратке '
				'высокотемпературного потребителя пройдена'
			)
			self._status = 'OK'
		finally:
			self.write_valve_running_time(original_valve_running_time)

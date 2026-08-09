from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario


class Scenario(DistrictHeatingScenario):
	OVER_TEMPERATURE_MARGIN = 5
	OVER_TEMPERATURE_DURATION = 2 * 60
	VALVE_RUNNING_TIME = 30
	VALVE_OBSERVATION_DURATION = 30
	MIN_VALVE_MOVEMENT = 10
	MIN_VALVE_POSITION = 10
	MIN_HOUSE_RETURN_MARGIN = 5

	def get_scenario_title(self):
		return 'District Heating: valve closes when city return is hotter than supply'

	def get_scenario_description(self):
		return (
			'Если температура обратки в город выше температуры подачи в город '
			'в течение двух минут, кран закрывается'
		)

	def get_checklist_id(self):
		return '3.12.5'

	def run(self):
		city_supply_sensor = self._district_heating.get_input_channel('supply_direct_temp')
		city_return_sensor = self._district_heating.get_input_channel('supply_backward_temp')
		house_return_sensor = self._district_heating.get_input_channel('backward_temp')
		analog_valve = self._district_heating.get_output_channel('analog_valve')

		for sensor, description in (
			(city_supply_sensor, 'датчик температуры подачи из города'),
			(city_return_sensor, 'датчик температуры обратки в город'),
			(house_return_sensor, 'датчик температуры обратки из дома'),
		):
			if not sensor.is_mapped():
				print_error(f'Не найден {description}')
				self._status = 'FAIL'
				return

		if not analog_valve.is_mapped():
			print_error('Не найден аналоговый выход крана')
			self._status = 'FAIL'
			return

		city_supply_temperature = city_supply_sensor.get_value()
		initial_valve = analog_valve.get_value()
		original_valve_running_time = self.read_valve_running_time()

		if city_supply_temperature is None:
			print_error('Не удалось получить температуру подачи из города')
			self._status = 'FAIL'
			return

		if initial_valve is None:
			print_error('Не удалось получить начальное положение крана')
			self._status = 'FAIL'
			return

		if initial_valve <= self.MIN_VALVE_POSITION:
			print_error(
				f'Кран уже закрыт (значение {initial_valve}), '
				'невозможно проверить его закрытие'
			)
			self._status = 'FAIL'
			return

		if original_valve_running_time is None:
			print_error('Не удалось получить исходное время хода крана')
			self._status = 'FAIL'
			return

		try:
			if self.write_valve_running_time(self.VALVE_RUNNING_TIME) is None:
				print_error('Не удалось изменить время хода крана')
				self._status = 'FAIL'
				return

			city_return_temperature = (
				city_supply_temperature + self.OVER_TEMPERATURE_MARGIN
			)
			house_return_temperature = (
				city_supply_temperature - self.MIN_HOUSE_RETURN_MARGIN
			)

			print_log(
				f'Устанавливаем температуру подачи из города '
				f'{city_supply_temperature:.1f} C'
			)
			self.set_sensor_value(city_supply_sensor, city_supply_temperature)

			print_log(
				f'Устанавливаем температуру обратки в город '
				f'{city_return_temperature:.1f} C, выше подачи на '
				f'{self.OVER_TEMPERATURE_MARGIN:.1f} C'
			)
			self.set_sensor_value(city_return_sensor, city_return_temperature)

			print_log(
				f'Устанавливаем температуру обратки из дома '
				f'{house_return_temperature:.1f} C, чтобы не активировать '
				'блокировку закрытия для высокотемпературного потребителя'
			)
			self.set_sensor_value(house_return_sensor, house_return_temperature)

			print_log(
				f'Ждём {self.OVER_TEMPERATURE_DURATION} секунд, '
				'пока высокая температура обратки обрабатывается'
			)
			self.wait(self.OVER_TEMPERATURE_DURATION)

			print_log(
				f'Проверяем закрытие крана ещё '
				f'{self.VALVE_OBSERVATION_DURATION} секунд'
			)
			self.wait(self.VALVE_OBSERVATION_DURATION)

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
					'Кран не начал закрываться после двух минут высокой '
					f'температуры обратки: изменение {movement} < '
					f'{self.MIN_VALVE_MOVEMENT}'
				)
				self._status = 'FAIL'
				return

			print_log(
				'Проверка закрытия крана при температуре обратки в город '
				'выше температуры подачи пройдена'
			)
			self._status = 'OK'
		finally:
			if self.write_valve_running_time(original_valve_running_time) is None:
				print_error('Не удалось восстановить исходное время хода крана')
				self._status = 'FAIL'

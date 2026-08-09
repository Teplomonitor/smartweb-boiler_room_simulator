from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc


class Scenario(DistrictHeatingScenario):
	OVER_TEMPERATURE_MARGIN = 5
	VALVE_CLOSE_TRIGGER_DURATION = 2 * 60
	VALVE_CLOSE_TIMEOUT = 3 * 60
	VALVE_CLOSED_POSITION = 10
	PUMP_OFF_DURATION = 30
	PUMP_OFF_TIMEOUT = 60
	PUMP_ON_DELAY = 60

	def get_scenario_title(self):
		return 'District Heating: loading pump switches off when valve is closed'

	def get_scenario_description(self):
		return (
			'Если кран ИТП закрыт, насос загрузки выключается и остаётся выключенным'
		)

	def get_checklist_id(self):
		return '3.12.7'

	def get_default_preset(self):
		return 'district_heating_3_12_7'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'outdoor': snc.ProgramType.OUTDOOR_SENSOR,
			'heatingCircuit': snc.ProgramType.HEATING_CIRCUIT,
		}

	def run(self):
		city_supply_sensor = self._district_heating.get_input_channel('supply_direct_temp')
		city_return_sensor = self._district_heating.get_input_channel('supply_backward_temp')
		house_return_sensor = self._district_heating.get_input_channel('backward_temp')
		analog_valve = self._district_heating.get_output_channel('analog_valve')
		loading_pump = self._district_heating.get_output_channel('supply_pump')

		for sensor, description in (
			(city_supply_sensor, 'датчик температуры подачи из города'),
			(city_return_sensor, 'датчик температуры обратки в город'),
			(house_return_sensor, 'датчик температуры обратки из дома'),
		):
			if not sensor.is_mapped():
				print_error(f'Не найден {description}')
				self._status = 'FAIL'
				return

		for channel, description in (
			(analog_valve, 'аналоговый выход крана'),
			(loading_pump, 'выход насоса загрузки'),
		):
			if not channel.is_mapped():
				print_error(f'Не найден {description}')
				self._status = 'FAIL'
				return
			
			
		print_log(
			f'Ждём, пока насос загрузки включится. Задержка на включение - {self.PUMP_ON_DELAY} секунд'
		)
		if not self.wait(self.PUMP_ON_DELAY + 10):
			self._status = 'FAIL'
			return
		
		city_supply_temperature = city_supply_sensor.get_value()
		initial_valve = analog_valve.get_value()
		initial_pump = loading_pump.get_value()

		if city_supply_temperature is None:
			print_error('Не удалось получить температуру подачи из города')
			self._status = 'FAIL'
			return

		if initial_valve is None:
			print_error('Не удалось получить начальное положение крана')
			self._status = 'FAIL'
			return

		if initial_valve <= self.VALVE_CLOSED_POSITION:
			print_error(
				f'Кран уже закрыт (значение {initial_valve}), '
				'невозможно проверить его закрытие'
			)
			self._status = 'FAIL'
			return

		if initial_pump is None:
			print_error('Не удалось получить начальное состояние насоса загрузки')
			self._status = 'FAIL'
			return

		if not initial_pump:
			print_error('Насос загрузки уже выключен, невозможно проверить его отключение')
			self._status = 'FAIL'
			return

		city_return_temperature = city_supply_temperature + self.OVER_TEMPERATURE_MARGIN
		house_return_temperature = city_supply_temperature - self.OVER_TEMPERATURE_MARGIN

		print_log(
			f'Устанавливаем температуру подачи из города {city_supply_temperature:.1f} C'
		)
		self.set_sensor_value(city_supply_sensor, city_supply_temperature)

		print_log(
			f'Устанавливаем температуру обратки в город {city_return_temperature:.1f} C, '
			'чтобы кран начал закрываться'
		)
		self.set_sensor_value(city_return_sensor, city_return_temperature)

		print_log(
			f'Устанавливаем температуру обратки из дома {house_return_temperature:.1f} C, '
			'чтобы не активировать блокировку закрытия крана'
		)
		self.set_sensor_value(house_return_sensor, house_return_temperature)

		print_log(
			f'Ждём {self.VALVE_CLOSE_TRIGGER_DURATION} секунд обработки высокой температуры обратки'
		)
		if not self.wait(self.VALVE_CLOSE_TRIGGER_DURATION):
			self._status = 'FAIL'
			return

		print_log(
			f'Ждём закрытия крана не более {self.VALVE_CLOSE_TIMEOUT} секунд'
		)
		if not self.wait_event(
			lambda: (
				analog_valve.get_value() is not None
				and analog_valve.get_value() <= self.VALVE_CLOSED_POSITION
			),
			self.VALVE_CLOSE_TIMEOUT,
		):
			print_error('Кран не закрылся за отведённое время')
			self._status = 'FAIL'
			return

		final_valve = analog_valve.get_value()
		print_log(f'Кран закрыт, текущее положение: {final_valve}')
		print_log(
			f'Проверяем выключение насоса загрузки в течение {self.PUMP_OFF_DURATION} секунд'
		)
		if not self.wait_state_permanence(
			lambda: loading_pump.get_value() == self.RELAY_OFF,
			self.PUMP_OFF_DURATION,
			self.PUMP_OFF_TIMEOUT,
		):
			pump_state = loading_pump.get_value()
			print_error(
				f'Насос загрузки не выключился при закрытом кране (состояние {pump_state})'
			)
			self._status = 'FAIL'
			return

		print_log('Проверка выключения насоса загрузки при закрытом кране пройдена')
		self._status = 'OK'

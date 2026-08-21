from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc
import smartnet.units as snu


class Scenario(DistrictHeatingScenario):
	COLD_SUPPLY_MARGIN = 10
	HOT_CITY_SUPPLY_TEMPERATURE = 50
	HOT_HOUSE_RETURN_MARGIN = 2
	STARTUP_TIMEOUT = 2 * 60
	STARTUP_STABILIZATION_DURATION = 20
	ON_DELAY_BUFFER = 30
	ON_RESPONSE_STABILIZATION_DURATION = 20
	ON_RESPONSE_TIMEOUT = 3 * 60
	OVERRIDE_RESPONSE_STABILIZATION_DURATION = 10
	OVERRIDE_RESPONSE_TIMEOUT = 90
	OFF_DELAY = 5 * 60

	def get_scenario_title(self):
		return 'District Heating: reserve generator work is disabled when house return is hot'

	def get_scenario_description(self):
		return (
			'Резервный генератор: запрещена работа, если температура обратки из дома '
			'выше "ТподачиГорода - 3К" (при подаче из города выше 35 C). Отключение '
			'происходит немедленно, минуя пятиминутную задержку на выключение'
		)

	def get_checklist_id(self):
		return '3.12.10.6'

	def get_default_preset(self):
		return 'district_heating_3_12_10'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'boiler': snc.ProgramType.BOILER,
			'circuit': snc.ProgramType.HEATING_CIRCUIT,
		}

	def run(self):
		self._boiler = self._programList['boiler']

		direct_temperature_sensor = self._district_heating.get_input_channel('direct_temp')
		city_supply_sensor = self._district_heating.get_input_channel('supply_direct_temp')
		house_return_sensor = self._district_heating.get_input_channel('backward_temp')

		for sensor, description in (
			(direct_temperature_sensor, 'датчик температуры подачи в дом'),
			(city_supply_sensor, 'датчик температуры подачи из города'),
			(house_return_sensor, 'датчик температуры обратки из дома'),
		):
			if not sensor.is_mapped():
				print_error(f'Не найден {description}')
				self._status = 'FAIL'
				return

		initial_direct_temperature = direct_temperature_sensor.get_value()
		initial_city_supply_temperature = city_supply_sensor.get_value()
		initial_house_return_temperature = house_return_sensor.get_value()
		initial_minimum_temperature_restriction = self.read_temperature_generator_parameter(
			self._boiler,
			snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
		)

		if initial_direct_temperature is None:
			print_error('Не удалось получить исходную температуру подачи в дом')
			self._status = 'FAIL'
			return

		if initial_city_supply_temperature is None:
			print_error('Не удалось получить исходную температуру подачи из города')
			self._status = 'FAIL'
			return

		if initial_house_return_temperature is None:
			print_error('Не удалось получить исходную температуру обратки из дома')
			self._status = 'FAIL'
			return

		if initial_minimum_temperature_restriction is None:
			print_error('Не удалось получить исходное ограничение минимальной температуры котла')
			self._status = 'FAIL'
			return

		print_log('Ждём 30 секунд для стабилизации требуемой температуры подачи в дом')
		self.wait(30)
		
		required_temperature = self.read_temperature_source_required_temperature(self._district_heating)

		if required_temperature is None or required_temperature in (0, snu.SENSOR_UNDEFINED):
			print_error(
				'У ИТП нет полноценного запроса на тепло от потребителя, '
				'невозможно разрешить работу резервного генератора для этой проверки'
			)
			self._status = 'FAIL'
			return

		power_request_delay = self.read_temperature_source_power_request_delay()

		if power_request_delay is None:
			print_error('Не удалось получить параметр "Задержка" (TemperatureSourcePowerRequestDelay)')
			self._status = 'FAIL'
			return

		try:
			if not self.write_temperature_generator_parameter(
				self._boiler,
				snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
				0,
			):
				print_error('Не удалось отключить ограничение минимальной температуры котла')
				self._status = 'FAIL'
				return

			print_log(
				f'Ждём исходное состояние ИТП (нет запроса резервному генератору) не более '
				f'{self.STARTUP_TIMEOUT} секунд'
			)
			if not self.wait_backup_generator_not_requested(
				self._boiler,
				self.STARTUP_STABILIZATION_DURATION,
				self.STARTUP_TIMEOUT,
			):
				print_error(
					'Резервный генератор уже запрошен изначально, '
					'сценарий не может подготовить условие для проверки'
				)
				self._status = 'FAIL'
				return

			cold_direct_temperature = required_temperature - self.COLD_SUPPLY_MARGIN
			print_log(
				f'Устанавливаем температуру подачи в дом {cold_direct_temperature:.1f} C, '
				'чтобы разрешить работу резервного генератора (холодная подача в дом)'
			)
			self.set_sensor_value(direct_temperature_sensor, cold_direct_temperature)

			on_delay_wait = power_request_delay + self.ON_DELAY_BUFFER
			print_log(
				f'Ждём задержку на включение "Задержка" плюс запас, всего {on_delay_wait:.0f} секунд'
			)
			if not self.wait(on_delay_wait):
				self._status = 'FAIL'
				return

			print_log(
				'Ждём разрешения работы резервного генератора не более '
				f'{self.ON_RESPONSE_TIMEOUT} секунд'
			)
			if not self.wait_backup_generator_requested(
				self._boiler,
				self.ON_RESPONSE_STABILIZATION_DURATION,
				self.ON_RESPONSE_TIMEOUT,
			):
				print_error(
					'Не удалось подготовить условие: ИТП не разрешил работу резервного '
					'генератора при холодной подаче в дом'
				)
				self._status = 'FAIL'
				return

			house_return_temperature = self.HOT_CITY_SUPPLY_TEMPERATURE - self.HOT_HOUSE_RETURN_MARGIN
			print_log(
				f'Устанавливаем температуру подачи из города {self.HOT_CITY_SUPPLY_TEMPERATURE:.1f} C '
				f'(выше 35 C) и температуру обратки из дома {house_return_temperature:.1f} C '
				'(не ниже ТподачиГорода-3К)'
			)
			self.set_sensor_value(city_supply_sensor, self.HOT_CITY_SUPPLY_TEMPERATURE)
			self.set_sensor_value(house_return_sensor, house_return_temperature)

			print_log(
				'Ждём немедленного запрета работы резервного генератора (минуя пятиминутную '
				f'задержку на выключение) не более {self.OVERRIDE_RESPONSE_TIMEOUT} секунд'
			)
			if not self.wait_backup_generator_not_requested(
				self._boiler,
				self.OVERRIDE_RESPONSE_STABILIZATION_DURATION,
				self.OVERRIDE_RESPONSE_TIMEOUT,
			):
				current_required_temperature = self.read_temperature_source_required_temperature(self._boiler)
				consumer_id = self.read_temperature_source_consumer_id(self._boiler)
				print_error(
					'ИТП не запретил работу резервного генератора при горячей обратке из дома: '
					f'требуемая температура={current_required_temperature}, '
					f'обслуживаемый потребитель={consumer_id}'
				)
				self._status = 'FAIL'
				return

			print_log(
				f'Резервный генератор отключился менее чем за {self.OVERRIDE_RESPONSE_TIMEOUT} '
				f'секунд, что значительно быстрее пятиминутной ({self.OFF_DELAY} секунд) '
				'обычной задержки на выключение'
			)
			self._status = 'OK'
		finally:
			self.set_sensor_value(direct_temperature_sensor, initial_direct_temperature)
			self.set_sensor_value(city_supply_sensor, initial_city_supply_temperature)
			self.set_sensor_value(house_return_sensor, initial_house_return_temperature)
			if not self.write_temperature_generator_parameter(
				self._boiler,
				snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
				initial_minimum_temperature_restriction,
			):
				print_error('Не удалось восстановить ограничение минимальной температуры котла')
				self._status = 'FAIL'

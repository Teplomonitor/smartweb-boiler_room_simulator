from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc


class Scenario(DistrictHeatingScenario):
	OVER_TEMPERATURE_MARGIN = 5
	VALVE_RUNNING_TIME = 30
	VALVE_CLOSE_TRIGGER_DURATION = 2 * 60
	VALVE_CLOSE_TIMEOUT = 5 * 60
	VALVE_POSITION_BELOW_HALF = 127
	VALVE_HALF_OPEN_MINIMUM = 114
	VALVE_HALF_OPEN_MAXIMUM = 140
	PERIODIC_OPEN_DURATION = 5 * 60
	PERIODIC_OPEN_TIMEOUT = 3 * 60 * 60
	REQUESTED_STABILIZATION_DURATION = 20
	REQUESTED_TIMEOUT = 3 * 60

	def get_scenario_title(self):
		return 'District Heating: reserve generator work is disabled during backward flow check'

	def get_scenario_description(self):
		return (
			'Резервный генератор: запрещена работа, если идёт периодическая проверка '
			'температуры обратки в город (кран приоткрывается до 50% на пять минут)'
		)

	def get_checklist_id(self):
		return '3.12.10.2'

	def get_default_preset(self):
		return 'district_heating_3_12_10'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'boiler': snc.ProgramType.BOILER,
		}

	def valve_is_below_half(self, valve):
		value = valve.get_value()
		return value is not None and value < self.VALVE_POSITION_BELOW_HALF

	def valve_is_half_open(self, valve):
		value = valve.get_value()
		return (
			value is not None
			and self.VALVE_HALF_OPEN_MINIMUM <= value <= self.VALVE_HALF_OPEN_MAXIMUM
		)

	def run(self):
		self._boiler = self._programList['boiler']

		city_supply_sensor = self._district_heating.get_input_channel('supply_direct_temp')
		city_return_sensor = self._district_heating.get_input_channel('supply_backward_temp')
		house_return_sensor = self._district_heating.get_input_channel('backward_temp')
		analog_valve = self._district_heating.get_output_channel('analog_valve')
		circulation_pump = self._district_heating.get_output_channel('circulation_pump')

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

		if not circulation_pump.is_mapped():
			print_error('Не найден выход циркуляционного насоса')
			self._status = 'FAIL'
			return

		city_supply_temperature = city_supply_sensor.get_value()
		initial_valve = analog_valve.get_value()
		original_valve_running_time = self.read_valve_running_time()
		initial_minimum_temperature_restriction = self.read_temperature_generator_parameter(
			self._boiler,
			snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
		)

		if city_supply_temperature is None:
			print_error('Не удалось получить температуру подачи из города')
			self._status = 'FAIL'
			return

		if initial_valve is None:
			print_error('Не удалось получить начальное положение крана')
			self._status = 'FAIL'
			return

		if original_valve_running_time is None:
			print_error('Не удалось получить исходное время хода крана')
			self._status = 'FAIL'
			return

		if initial_minimum_temperature_restriction is None:
			print_error('Не удалось получить исходное ограничение минимальной температуры котла')
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

			if self.write_valve_running_time(self.VALVE_RUNNING_TIME) is None:
				print_error('Не удалось изменить время хода крана')
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
				f'Ждём положения крана менее 50% не более {self.VALVE_CLOSE_TIMEOUT} секунд'
			)
			if not self.wait_event(
				lambda: self.valve_is_below_half(analog_valve),
				self.VALVE_CLOSE_TIMEOUT,
			):
				print_error('Кран не перешёл в положение менее 50% за отведённое время')
				self._status = 'FAIL'
				return

			initial_low_position = analog_valve.get_value()
			print_log(
				'Проверяем, что перед периодической проверкой резервный генератор запрошен, '
				f'не более {self.REQUESTED_TIMEOUT} секунд'
			)
			if not self.wait_backup_generator_requested(
				self._boiler,
				self.REQUESTED_STABILIZATION_DURATION,
				self.REQUESTED_TIMEOUT,
			):
				required_temperature = self.read_temperature_source_required_temperature(self._boiler)
				consumer_id = self.read_temperature_source_consumer_id(self._boiler)
				print_error(
					'Не удалось подготовить включённое состояние резервного генератора перед '
					f'периодической проверкой: требуемая температура={required_temperature}, '
					f'обслуживаемый потребитель={consumer_id}'
				)
				self._status = 'FAIL'
				return

			print_log(
				f'Кран открыт менее чем на 50% (положение {initial_low_position}). '
				f'Ждём периодической проверки обратного потока в течение трёх часов '
				f'(не более {self.PERIODIC_OPEN_TIMEOUT} секунд)'
			)
			if not self.wait_event(
				lambda: self.valve_is_half_open(analog_valve),
				self.PERIODIC_OPEN_TIMEOUT,
			):
				final_valve = analog_valve.get_value()
				print_error(
					f'Кран не открылся примерно до 50% за три часа '
					f'(положение {final_valve}), проверка обратного потока не наступила'
				)
				self._status = 'FAIL'
				return

			opened_valve = analog_valve.get_value()
			print_log(
				f'Кран приоткрыт до положения {opened_valve} — идёт проверка обратного потока. '
				f'Проверяем запрет работы резервного генератора и выключение циркуляционного '
				f'насоса в течение {self.PERIODIC_OPEN_DURATION} секунд'
			)
			if not self.wait_state_permanence(
				lambda: (
					self.valve_is_half_open(analog_valve)
					and circulation_pump.get_value() == self.RELAY_OFF
					and self.backup_generator_is_not_requested(self._boiler) is True
				),
				self.PERIODIC_OPEN_DURATION,
				self.PERIODIC_OPEN_DURATION,
			):
				final_valve = analog_valve.get_value()
				pump_state = circulation_pump.get_value()
				required_temperature = self.read_temperature_source_required_temperature(self._boiler)
				print_error(
					'Во время проверки обратного потока состояние не соответствовало ожиданиям: '
					f'положение крана {final_valve}, состояние насоса {pump_state}, '
					f'требуемая температура резервного генератора {required_temperature}'
				)
				self._status = 'FAIL'
				return

			print_log(
				'Проверка запрета работы резервного генератора во время проверки '
				'обратного потока пройдена'
			)
			self._status = 'OK'
		finally:
			if self.write_valve_running_time(original_valve_running_time) is None:
				print_error('Не удалось восстановить исходное время хода крана')
				self._status = 'FAIL'
			if not self.write_temperature_generator_parameter(
				self._boiler,
				snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
				initial_minimum_temperature_restriction,
			):
				print_error('Не удалось восстановить ограничение минимальной температуры котла')
				self._status = 'FAIL'

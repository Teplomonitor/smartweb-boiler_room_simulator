from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc


class Scenario(DistrictHeatingScenario):
	COLD_SUPPLY_MARGIN = 5
	STARTUP_TIMEOUT = 2 * 60
	STARTUP_STABILIZATION_DURATION = 20
	BLOCK_TRIGGER_DURATION = 2 * 60
	RESPONSE_TIMEOUT = 3 * 60
	RESPONSE_STABILIZATION_DURATION = 20

	def get_scenario_title(self):
		return 'District Heating: reserve generator work is enabled when city supply is cold'

	def get_scenario_description(self):
		return (
			'Резервный генератор: разрешена работа, если температура подачи из города '
			'холодная (ниже температуры обратки в город) в течение двух минут'
		)

	def get_checklist_id(self):
		return '3.12.10.3'

	def get_default_preset(self):
		return 'district_heating_3_12_10'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'boiler': snc.ProgramType.BOILER,
		}

	def run(self):
		self._boiler = self._programList['boiler']

		city_supply_sensor = self._district_heating.get_input_channel('supply_direct_temp')
		city_return_sensor = self._district_heating.get_input_channel('supply_backward_temp')

		for sensor, description in (
			(city_supply_sensor, 'датчик температуры подачи из города'),
			(city_return_sensor, 'датчик температуры обратки в город'),
		):
			if not sensor.is_mapped():
				print_error(f'Не найден {description}')
				self._status = 'FAIL'
				return

		initial_city_supply_temperature = city_supply_sensor.get_value()
		initial_city_return_temperature = city_return_sensor.get_value()
		initial_minimum_temperature_restriction = self.read_temperature_generator_parameter(
			self._boiler,
			snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
		)

		if initial_city_supply_temperature is None:
			print_error('Не удалось получить исходную температуру подачи из города')
			self._status = 'FAIL'
			return

		if initial_city_return_temperature is None:
			print_error('Не удалось получить исходную температуру обратки в город')
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
					'Резервный генератор уже запрошен до создания холодной подачи из города, '
					'сценарий не может проверить включение по холодной подаче'
				)
				self._status = 'FAIL'
				return

			city_return_temperature = initial_city_supply_temperature
			city_supply_temperature = city_return_temperature - self.COLD_SUPPLY_MARGIN

			print_log(
				f'Устанавливаем температуру обратки в город {city_return_temperature:.1f} C'
			)
			self.set_sensor_value(city_return_sensor, city_return_temperature)

			print_log(
				f'Устанавливаем температуру подачи из города {city_supply_temperature:.1f} C '
				'(ниже обратки в город), чтобы подача считалась холодной'
			)
			self.set_sensor_value(city_supply_sensor, city_supply_temperature)

			print_log(
				f'Ждём {self.BLOCK_TRIGGER_DURATION} секунд, пока холодная подача из города '
				'не будет засчитана непрерывной'
			)
			if not self.wait(self.BLOCK_TRIGGER_DURATION):
				self._status = 'FAIL'
				return

			print_log(
				'Ждём разрешения работы резервного генератора (требуемая температура > 0 '
				f'и ИТП — обслуживаемый потребитель) не более {self.RESPONSE_TIMEOUT} секунд'
			)
			if not self.wait_backup_generator_requested(
				self._boiler,
				self.RESPONSE_STABILIZATION_DURATION,
				self.RESPONSE_TIMEOUT,
			):
				required_temperature = self.read_temperature_source_required_temperature(self._boiler)
				consumer_id = self.read_temperature_source_consumer_id(self._boiler)
				print_error(
					'ИТП не разрешил работу резервного генератора при холодной подаче из города: '
					f'требуемая температура={required_temperature}, '
					f'обслуживаемый потребитель={consumer_id}, '
					f'ожидался ИТП с id={self._district_heating.get_id()}'
				)
				self._status = 'FAIL'
				return

			print_log(
				'ИТП разрешил работу резервного генератора при холодной подаче из города'
			)
			self._status = 'OK'
		finally:
			self.set_sensor_value(city_supply_sensor, initial_city_supply_temperature)
			self.set_sensor_value(city_return_sensor, initial_city_return_temperature)
			if not self.write_temperature_generator_parameter(
				self._boiler,
				snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
				initial_minimum_temperature_restriction,
			):
				print_error('Не удалось восстановить ограничение минимальной температуры котла')
				self._status = 'FAIL'

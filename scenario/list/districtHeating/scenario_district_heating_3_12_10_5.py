from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc
import smartnet.units as snu


class Scenario(DistrictHeatingScenario):
	COLD_SUPPLY_MARGIN = 10
	STARTUP_TIMEOUT = 2 * 60
	STARTUP_STABILIZATION_DURATION = 20
	ON_DELAY_BUFFER = 30
	ON_RESPONSE_STABILIZATION_DURATION = 20
	ON_RESPONSE_TIMEOUT = 3 * 60
	OFF_DELAY_HOLD_DURATION = 4 * 60
	OFF_RESPONSE_STABILIZATION_DURATION = 20
	OFF_RESPONSE_TIMEOUT = 3 * 60

	def get_scenario_title(self):
		return 'District Heating: reserve generator work is enabled when house supply is cold'

	def get_scenario_description(self):
		return (
			'Резервный генератор: разрешена работа, если подача в дом холодная '
			'(температура подачи в дом меньше требуемой более чем на 5К). '
			'Задержка на включение резервного генератора равна параметру "Задержка" '
			'(TemperatureSourcePowerRequestDelay), задержка на выключение — 5 минут'
		)

	def get_checklist_id(self):
		return '3.12.10.5'

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

		if not direct_temperature_sensor.is_mapped():
			print_error('Не найден датчик температуры подачи в дом')
			self._status = 'FAIL'
			return

		initial_direct_temperature = direct_temperature_sensor.get_value()
		initial_minimum_temperature_restriction = self.read_temperature_generator_parameter(
			self._boiler,
			snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
		)

		if initial_direct_temperature is None:
			print_error('Не удалось получить исходную температуру подачи в дом')
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
				'невозможно проверить холодную подачу в дом'
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
					'Резервный генератор уже запрошен до создания холодной подачи в дом, '
					'сценарий не может проверить включение по холодной подаче'
				)
				self._status = 'FAIL'
				return

			cold_direct_temperature = required_temperature - self.COLD_SUPPLY_MARGIN
			print_log(
				f'Устанавливаем температуру подачи в дом {cold_direct_temperature:.1f} C '
				f'(требуемая температура {required_temperature:.1f} C минус '
				f'{self.COLD_SUPPLY_MARGIN} K), чтобы подача считалась холодной'
			)
			self.set_sensor_value(direct_temperature_sensor, cold_direct_temperature)

			on_delay_wait = power_request_delay + self.ON_DELAY_BUFFER
			print_log(
				f'Ждём задержку на включение "Задержка" ({power_request_delay:.0f} секунд) '
				f'плюс запас, всего {on_delay_wait:.0f} секунд'
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
				current_required_temperature = self.read_temperature_source_required_temperature(self._boiler)
				consumer_id = self.read_temperature_source_consumer_id(self._boiler)
				print_error(
					'ИТП не разрешил работу резервного генератора при холодной подаче в дом: '
					f'требуемая температура={current_required_temperature}, '
					f'обслуживаемый потребитель={consumer_id}'
				)
				self._status = 'FAIL'
				return

			print_log('Восстанавливаем нормальную температуру подачи в дом')
			self.set_sensor_value(direct_temperature_sensor, initial_direct_temperature)

			print_log(
				'Проверяем, что резервный генератор остаётся включённым в течение '
				f'{self.OFF_DELAY_HOLD_DURATION} секунд (меньше задержки на выключение 5 минут)'
			)
			if not self.wait_backup_generator_requested(
				self._boiler,
				self.OFF_DELAY_HOLD_DURATION,
				self.OFF_DELAY_HOLD_DURATION,
			):
				print_error(
					'Резервный генератор выключился раньше задержки на выключение (5 минут)'
				)
				self._status = 'FAIL'
				return

			print_log(
				'Ждём выключения резервного генератора после задержки на выключение (5 минут) '
				f'не более {self.OFF_RESPONSE_TIMEOUT} секунд'
			)
			if not self.wait_backup_generator_not_requested(
				self._boiler,
				self.OFF_RESPONSE_STABILIZATION_DURATION,
				self.OFF_RESPONSE_TIMEOUT,
			):
				print_error(
					'Резервный генератор не выключился после задержки на выключение (5 минут)'
				)
				self._status = 'FAIL'
				return

			print_log(
				'Проверка включения/выключения резервного генератора по холодной подаче '
				'в дом пройдена'
			)
			self._status = 'OK'
		finally:
			self.set_sensor_value(direct_temperature_sensor, initial_direct_temperature)
			if not self.write_temperature_generator_parameter(
				self._boiler,
				snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
				initial_minimum_temperature_restriction,
			):
				print_error('Не удалось восстановить ограничение минимальной температуры котла')
				self._status = 'FAIL'

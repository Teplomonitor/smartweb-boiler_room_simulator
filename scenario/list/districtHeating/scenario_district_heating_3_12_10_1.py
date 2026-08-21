from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc


class Scenario(DistrictHeatingScenario):
	STARTUP_TIMEOUT = 2 * 60
	STARTUP_STABILIZATION_DURATION = 20
	ALARM_RESPONSE_TIMEOUT = 3 * 60
	ALARM_RESPONSE_STABILIZATION_DURATION = 30

	def get_scenario_title(self):
		return 'District Heating: reserve generator work is enabled by an alarm signal'

	def get_scenario_description(self):
		return (
			'Резервный генератор: разрешена работа, если ИТП получил сигнал аварии '
			'от аварийной программы'
		)

	def get_checklist_id(self):
		return '3.12.10.1'

	def get_default_preset(self):
		return 'district_heating_3_12_10'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'boiler': snc.ProgramType.BOILER,
			'circuit': snc.ProgramType.HEATING_CIRCUIT,
			'alarm': snc.ProgramType.FILLING_LOOP,
		}

	def run(self):
		self._boiler = self._programList['boiler']
		self._alarm = self._programList['alarm']
		pressure_sensor = self._alarm.getPressure()

		if not pressure_sensor.is_mapped():
			print_error('Не найден датчик давления программы подпитки')
			self._status = 'FAIL'
			return

		initial_minimum_temperature_restriction = self.read_temperature_generator_parameter(
			self._boiler,
			snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
		)
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
					'Резервный генератор уже запрошен до подачи сигнала аварии, '
					'сценарий не может проверить включение по аварии'
				)
				self._status = 'FAIL'
				return

			print_log('Подаём сигнал аварии: низкое давление в программе подпитки')
			self.set_sensor_value(pressure_sensor, 'open')

			print_log(
				'Ждём разрешения работы резервного генератора (требуемая температура > 0 '
				f'и ИТП — обслуживаемый потребитель) не более {self.ALARM_RESPONSE_TIMEOUT} секунд'
			)
			if not self.wait_backup_generator_requested(
				self._boiler,
				self.ALARM_RESPONSE_STABILIZATION_DURATION,
				self.ALARM_RESPONSE_TIMEOUT,
			):
				required_temperature = self.read_temperature_source_required_temperature(self._boiler)
				consumer_id = self.read_temperature_source_consumer_id(self._boiler)
				print_error(
					'ИТП не разрешил работу резервного генератора по сигналу аварии: '
					f'требуемая температура={required_temperature}, '
					f'обслуживаемый потребитель={consumer_id}, '
					f'ожидался ИТП с id={self._district_heating.get_id()}'
				)
				self._status = 'FAIL'
				return

			print_log(
				'ИТП разрешил работу резервного генератора по сигналу аварии'
			)
			self._status = 'OK'
		finally:
			self.set_sensor_value(pressure_sensor, 'short')
			if not self.write_temperature_generator_parameter(
				self._boiler,
				snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
				initial_minimum_temperature_restriction,
			):
				print_error('Не удалось восстановить ограничение минимальной температуры котла')
				self._status = 'FAIL'

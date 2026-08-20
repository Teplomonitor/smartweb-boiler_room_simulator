from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc


class Scenario(DistrictHeatingScenario):
	SATISFIED_TANK_TEMPERATURE = 90
	NO_REQUEST_STABILIZATION_DURATION = 30
	NO_REQUEST_TIMEOUT = 3 * 60
	DISABLED_STABILIZATION_DURATION = 30
	DISABLED_TIMEOUT = 2 * 60

	def get_scenario_title(self):
		return 'District Heating: reserve generator work is disabled when there is no heat request'

	def get_scenario_description(self):
		return (
			'Резервный генератор: запрещена работа, если у ИТП нет запроса на тепло от потребителя'
		)

	def get_checklist_id(self):
		return '3.12.10.4'

	def get_default_preset(self):
		return 'district_heating_3_12_10'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'boiler': snc.ProgramType.BOILER,
			'dhw': snc.ProgramType.DHW,
		}

	def run(self):
		self._boiler = self._programList['boiler']
		dhw = self._programList['dhw']

		tank_sensor = dhw.get_input_channel('temperature')

		if not tank_sensor.is_mapped():
			print_error('Не найден датчик температуры бойлера ГВС')
			self._status = 'FAIL'
			return

		initial_tank_temperature = tank_sensor.get_value()

		if initial_tank_temperature is None:
			print_error('Не удалось получить исходную температуру бойлера ГВС')
			self._status = 'FAIL'
			return

		try:
			print_log(
				f'Устанавливаем температуру бойлера ГВС {self.SATISFIED_TANK_TEMPERATURE} C, '
				'чтобы потребитель перестал запрашивать тепло у ИТП'
			)
			self.set_sensor_value(tank_sensor, self.SATISFIED_TANK_TEMPERATURE)

			print_log(
				f'Ждём, пока у ИТП пропадёт запрос на тепло от потребителя, не более '
				f'{self.NO_REQUEST_TIMEOUT} секунд'
			)
			if not self.wait_state_permanence(
				lambda: self.backup_generator_is_not_requested(self._district_heating) is True,
				self.NO_REQUEST_STABILIZATION_DURATION,
				self.NO_REQUEST_TIMEOUT,
			):
				required_temperature = self.read_temperature_source_required_temperature(self._district_heating)
				print_error(
					'Потребитель (ГВС) продолжает запрашивать тепло у ИТП: '
					f'требуемая температура={required_temperature}'
				)
				self._status = 'FAIL'
				return

			print_log(
				'Проверяем запрет работы резервного генератора при отсутствии запроса на тепло '
				f'не более {self.DISABLED_TIMEOUT} секунд'
			)
			if not self.wait_state_permanence(
				lambda: self.backup_generator_is_not_requested(self._boiler) is True,
				self.DISABLED_STABILIZATION_DURATION,
				self.DISABLED_TIMEOUT,
			):
				required_temperature = self.read_temperature_source_required_temperature(self._boiler)
				consumer_id = self.read_temperature_source_consumer_id(self._boiler)
				print_error(
					'ИТП разрешил работу резервного генератора при отсутствии запроса на тепло: '
					f'требуемая температура={required_temperature}, '
					f'обслуживаемый потребитель={consumer_id}'
				)
				self._status = 'FAIL'
				return

			print_log(
				'ИТП не разрешает работу резервного генератора при отсутствии запроса на тепло'
			)
			self._status = 'OK'
		finally:
			self.set_sensor_value(tank_sensor, initial_tank_temperature)

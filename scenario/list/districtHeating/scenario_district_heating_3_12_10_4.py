from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc


class Scenario(DistrictHeatingScenario):
	REQUESTING_CIRCUIT_TEMPERATURE = 45
	TEMPERATURE_COMPENSATION = 5
	CONSTANT_TEMPERATURE_MODE = snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE
	DISCONNECTED_GENERATOR_ID = 107
	REQUESTED_STABILIZATION_DURATION = 20
	REQUESTED_TIMEOUT = 3 * 60
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
			'circuit': snc.ProgramType.HEATING_CIRCUIT,
		}

	def run(self):
		self._boiler = self._programList['boiler']
		circuit = self._programList['circuit']
		initial_minimum_temperature_restriction = self.read_temperature_generator_parameter(
			self._boiler,
			snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
		)
		initial_heat_calculation_mode = self.read_circuit_heat_calculation_mode(circuit)
		initial_constant_flow_temperature = self.read_circuit_required_constant_flow_temperature(circuit)
		initial_temperature_compensation = self.read_circuit_temperature_compensation(circuit)
		initial_generator_id = self.read_circuit_generator_id(circuit)

		if initial_minimum_temperature_restriction is None:
			print_error('Не удалось получить исходное ограничение минимальной температуры котла')
			self._status = 'FAIL'
			return

		if (
			initial_heat_calculation_mode is None
			or initial_constant_flow_temperature is None
			or initial_temperature_compensation is None
			or initial_generator_id is None
		):
			print_error('Не удалось получить исходные параметры контура отопления')
			self._status = 'FAIL'
			return

		try:
			for parameter, value, description in (
				('mode', self.CONSTANT_TEMPERATURE_MODE, 'режим постоянной температуры'),
				('temperature', self.REQUESTING_CIRCUIT_TEMPERATURE, 'температуру постоянного потока'),
				('compensation', self.TEMPERATURE_COMPENSATION, 'температурную компенсацию'),
			):
				if parameter == 'mode':
					result = self.write_circuit_heat_calculation_mode(circuit, value)
				elif parameter == 'temperature':
					result = self.write_circuit_required_constant_flow_temperature(circuit, value)
				else:
					result = self.write_circuit_temperature_compensation(circuit, value)
				if result is None:
					print_error(f'Не удалось установить {description}')
					self._status = 'FAIL'
					return

			if not self.write_temperature_generator_parameter(
				self._boiler,
				snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
				0,
			):
				print_error('Не удалось отключить ограничение минимальной температуры котла')
				self._status = 'FAIL'
				return

			print_log(
				f'Устанавливаем температуру постоянного потока контура '
				f'{self.REQUESTING_CIRCUIT_TEMPERATURE} C '
				'чтобы резервный генератор получил запрос на тепло'
			)

			print_log(
				'Ждём устойчивого запроса резервному генератору перед проверкой выключения, '
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
					'Не удалось подготовить включённое состояние резервного генератора: '
					f'требуемая температура={required_temperature}, обслуживаемый потребитель={consumer_id}'
				)
				self._status = 'FAIL'
				return

			print_log(
				f'Отключаем контур от ИТП: устанавливаем несуществующий номер генератора '
				f'{self.DISCONNECTED_GENERATOR_ID}'
			)
			if self.write_circuit_generator_id(circuit, self.DISCONNECTED_GENERATOR_ID) is None:
				print_error('Не удалось отключить контур отопления от ИТП')
				self._status = 'FAIL'
				return

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
					'Контур отопления продолжает запрашивать тепло у ИТП: '
					f'требуемая температура={required_temperature}'
				)
				self._status = 'FAIL'
				return

			print_log(
				'Проверяем запрет работы резервного генератора при отсутствии запроса на тепло '
				f'не более {self.DISABLED_TIMEOUT} секунд'
			)
			if not self.wait_backup_generator_not_requested(
				self._boiler,
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
			if self.write_circuit_generator_id(circuit, initial_generator_id) is None:
				print_error('Не удалось восстановить номер генератора контура отопления')
				self._status = 'FAIL'
			if self.write_circuit_heat_calculation_mode(circuit, initial_heat_calculation_mode) is None:
				print_error('Не удалось восстановить режим расчёта контура отопления')
				self._status = 'FAIL'
			if self.write_circuit_required_constant_flow_temperature(
				circuit,
				initial_constant_flow_temperature,
			) is None:
				print_error('Не удалось восстановить постоянную температуру контура отопления')
				self._status = 'FAIL'
			if self.write_circuit_temperature_compensation(circuit, initial_temperature_compensation) is None:
				print_error('Не удалось восстановить температурную компенсацию контура отопления')
				self._status = 'FAIL'
			if not self.write_temperature_generator_parameter(
				self._boiler,
				snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
				initial_minimum_temperature_restriction,
			):
				print_error('Не удалось восстановить ограничение минимальной температуры котла')
				self._status = 'FAIL'

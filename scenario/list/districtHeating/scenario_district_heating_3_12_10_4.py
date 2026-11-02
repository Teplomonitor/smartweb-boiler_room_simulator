from consoleLog import print_log
from scenario.base.district_heating_checks import DistrictHeatingChecks
import smartnet.constants as snc


class Scenario(DistrictHeatingChecks):
	ESTIMATED_RUN_SECONDS = 420
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
	COLD_CITY_SUPPLY = 25
	CITY_RETURN = 30

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
		boiler = self._programList['boiler']
		circuit = self._programList['circuit']
		settings = (
			(boiler, 'minimumTemperatureRestriction', 0),
			(circuit, 'generatorId', self._district_heating.get_id()),
			(circuit, 'heatCalculationMode', self.CONSTANT_TEMPERATURE_MODE),
			(circuit, 'requiredConstantFlowTemperature', self.REQUESTING_CIRCUIT_TEMPERATURE),
			(circuit, 'temperatureCompensation', self.TEMPERATURE_COMPENSATION),
		)
		with self.conditions(self.temperature_sensors(), settings) as ready:
			if not ready:
				return
			for sensor, value in zip(self.temperature_sensors(), (
				self.COLD_CITY_SUPPLY, self.CITY_RETURN,
				self.REQUESTING_CIRCUIT_TEMPERATURE + self.TEMPERATURE_COMPENSATION,
				self.NORMAL_HOUSE_RETURN)):
				self.set_sensor_value(sensor, value)
			print_log('Городская подача ниже обратки: подтверждаем запрос резерва')
			self.require(self.wait_backup_generator_requested(boiler,
				self.REQUESTED_STABILIZATION_DURATION, self.REQUESTED_TIMEOUT),
				'Не удалось создать запрос резерва при холодном городском источнике')
			self.require(circuit.write_parameter('generatorId', self.DISCONNECTED_GENERATOR_ID),
				'Не удалось отключить потребителя от ИТП')
			self.require(self.wait_backup_generator_not_requested(self._district_heating,
				self.NO_REQUEST_STABILIZATION_DURATION, self.NO_REQUEST_TIMEOUT),
				'Запрос потребителя к ИТП не прекратился')
			self.require(self.wait_backup_generator_not_requested(boiler,
				self.DISABLED_STABILIZATION_DURATION, self.DISABLED_TIMEOUT),
				'Резерв продолжает получать запрос без потребителя')
			self._status = 'OK'
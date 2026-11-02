from consoleLog import print_log
from scenario.base.district_heating_checks import DistrictHeatingChecks
import smartnet.constants as snc


class Scenario(DistrictHeatingChecks):
	ESTIMATED_RUN_SECONDS = 900
	REQUIRED_TEMPERATURE = 50
	WARM_SUPPLY_MARGIN = 5
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
		boiler = self._programList['boiler']
		circuit = self._programList['circuit']
		settings = (
			(boiler, 'minimumTemperatureRestriction', 0),
			(circuit, 'generatorId', self._district_heating.get_id()),
			(circuit, 'heatCalculationMode', snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE),
			(circuit, 'requiredConstantFlowTemperature', self.REQUIRED_TEMPERATURE),
			(circuit, 'temperatureCompensation', 0),
		)
		with self.conditions(self.temperature_sensors(), settings) as ready:
			if not ready:
				return
			warm_supply = self.REQUIRED_TEMPERATURE + self.WARM_SUPPLY_MARGIN
			for sensor, value in zip(self.temperature_sensors(), (
				self.CITY_SUPPLY, self.NORMAL_CITY_RETURN, warm_supply, self.NORMAL_HOUSE_RETURN)):
				self.set_sensor_value(sensor, value)
			self.require(self.wait_until(lambda: self.read_temperature_source_required_temperature(
				self._district_heating) == self.REQUIRED_TEMPERATURE, self.STARTUP_TIMEOUT),
				'ИТП не получил заданную уставку потребителя')
			delay = self.read_temperature_source_power_request_delay()
			self.require(isinstance(delay, (int, float)) and 0 <= delay <= self.MAXIMUM_ON_DELAY,
				'Не прочитана допустимая задержка включения резерва')
			self.require(self.wait_backup_generator_not_requested(boiler,
				self.STARTUP_STABILIZATION_DURATION, self.STARTUP_TIMEOUT), 'Резерв уже запрошен до недогрева')
			direct = self._district_heating.get_input_channel('direct_temp')
			self.set_sensor_value(direct, self.REQUIRED_TEMPERATURE - self.COLD_SUPPLY_MARGIN)
			print_log(f'Создан недогрев; задержка включения резерва {delay:g} с')
			self.require(self.wait(delay + self.ON_DELAY_BUFFER), 'Проверка прервана')
			self.require(self.wait_backup_generator_requested(boiler,
				self.ON_RESPONSE_STABILIZATION_DURATION, self.ON_RESPONSE_TIMEOUT), 'Резерв не включился при недогреве')
			print_log(f'Устраняем недогрев: подача {warm_supply} C, уставка {self.REQUIRED_TEMPERATURE} C')
			self.set_sensor_value(direct, warm_supply)
			self.require(self.wait_backup_generator_requested(boiler,
				self.OFF_DELAY_HOLD_DURATION, self.OFF_DELAY_HOLD_DURATION), 'Резерв отключился раньше пяти минут')
			self.require(self.wait_backup_generator_not_requested(boiler,
				self.OFF_RESPONSE_STABILIZATION_DURATION, self.OFF_RESPONSE_TIMEOUT),
				'Недогрев устранён, но резерв не отключился: проверить удержание preheat в прошивке')
			self._status = 'OK'
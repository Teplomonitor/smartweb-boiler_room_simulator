from consoleLog import print_log
from scenario.base.district_heating_checks import DistrictHeatingChecks
import smartnet.constants as snc


class Scenario(DistrictHeatingChecks):
	ESTIMATED_RUN_SECONDS = 840
	REQUIRED_TEMPERATURE = 50
	WARM_SUPPLY_MARGIN = 5
	COLD_SUPPLY_MARGIN = 10
	STARTUP_TIMEOUT = 2 * 60
	STARTUP_STABILIZATION_DURATION = 20
	ON_DELAY_BUFFER = 30
	ON_RESPONSE_STABILIZATION_DURATION = 20
	ON_RESPONSE_TIMEOUT = 3 * 60
	PREHEAT_HOLD_DURATION = 6 * 60

	def get_scenario_title(self):
		return 'District Heating: compatibility preheat starts on cold supply and remains enabled after recovery'

	def get_scenario_description(self):
		return (
			'Совместимость: разрешена работа резерва, если подача в дом холодная '
			'(температура подачи в дом меньше требуемой более чем на 5К). '
			'Задержка на включение резервного генератора равна параметру "Задержка" '
			'(TemperatureSourcePowerRequestDelay). При исправных датчиках устранение '
			'недогрева не снимает запрос: подогрев сохраняется более пяти минут, '
			'пока обратка дома ниже температуры подачи города минус 3 K'
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
			(self._district_heating, 'reserveMode', snc.DistrictHeatingReserveMode.COMPATIBILITY),
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
			print_log(f'Проверяем сохранение запроса подогрева {self.PREHEAT_HOLD_DURATION} с '
				'при исправных датчиках и низкой обратке дома')
			# No acquisition timeout: a lost request must fail, not be reacquired.
			self.require(self.wait_backup_generator_requested(boiler,
				self.PREHEAT_HOLD_DURATION, 0),
				'Совместимость: запрос подогрева снят после устранения недогрева при низкой обратке дома')
			self._status = 'OK'
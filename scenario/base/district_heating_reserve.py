from scenario.base.district_heating_checks import DistrictHeatingChecks
import smartnet.constants as snc


class DistrictHeatingReserveChecks(DistrictHeatingChecks):
	REQUIRED_TEMPERATURE = 50
	WARM_SUPPLY = 55
	COLD_SUPPLY = 40
	RESERVE_ON_DELAY = 15
	TRANSITION_TIMEOUT = 180
	STABLE_DURATION = 10
	ISOLATION_OBSERVATION = 30
	DISCONNECTED_GENERATOR_ID = 250
	ESTIMATED_RUN_SECONDS = 600

	def get_required_programs(self):
		return {'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'boiler': snc.ProgramType.BOILER, 'circuit': snc.ProgramType.HEATING_CIRCUIT}

	def force_preset_load(self):
		return True

	def run_reserve_mode_check(self, mode):
		boiler, circuit = self._programList['boiler'], self._programList['circuit']
		city_alarm = self._district_heating.get_input_channel('city_alarm')
		valve = self._district_heating.get_output_channel('analog_valve')
		reserve_valves = self._district_heating.get_output_channel('reserve_valves')
		settings = (
			(self._district_heating, 'reserveMode', snc.DistrictHeatingReserveMode.COMPATIBILITY),
			(self._district_heating, 'valveRunningTime', self.VALVE_RUNNING_TIME),
			(self._district_heating, 'temperatureSourcePowerRequestDelay', self.RESERVE_ON_DELAY),
			(boiler, 'minimumTemperatureRestriction', 0),
			(circuit, 'generatorId', self._district_heating.get_id()),
			(circuit, 'heatCalculationMode', snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE),
			(circuit, 'requiredConstantFlowTemperature', self.REQUIRED_TEMPERATURE),
			(circuit, 'temperatureCompensation', 0),
		)
		with self.conditions(self.temperature_sensors() + (city_alarm,), settings) as ready:
			if not ready:
				return
			self.require(valve.is_mapped() and reserve_valves.is_mapped(), 'Не назначены КЗР и краны резерва')
			self.set_sensor_value(city_alarm, 'open')
			for sensor, value in zip(self.temperature_sensors(), (
				self.CITY_SUPPLY, self.NORMAL_CITY_RETURN, self.WARM_SUPPLY, self.NORMAL_HOUSE_RETURN)):
				self.set_sensor_value(sensor, value)
			self.require(self.wait_until(lambda: self.read_temperature_source_required_temperature(
				self._district_heating) == self.REQUIRED_TEMPERATURE, self.STARTUP_TIMEOUT),
				'Не подтверждён запрос потребителя к ИТП')
			self.require(self._district_heating.write_parameter('reserveMode', mode), 'Не записан режим резерва')
			self.require(self.wait_backup_generator_not_requested(boiler, self.STABLE_DURATION,
				self.TRANSITION_TIMEOUT), 'Резерв запрошен при достаточном городском источнике')
			self.set_sensor_value(self.temperature_sensors()[2], self.COLD_SUPPLY)
			self.require(self.wait_backup_generator_requested(boiler, self.STABLE_DURATION,
				self.TRANSITION_TIMEOUT), 'Резерв не включился при длительном недогреве')
			isolated = mode == snc.DistrictHeatingReserveMode.RESERVE_ONLY
			self.require(self.wait_state_permanence(lambda:
				reserve_valves.get_value() == self.RELAY_ON and valve.get_value() is not None
				and ((valve.get_value() == self.RELAY_OFF) if isolated else valve.get_value() > self.RELAY_OFF),
				self.STABLE_DURATION, self.TRANSITION_TIMEOUT), 'Неверное состояние КЗР или кранов резерва')
			self.set_sensor_value(city_alarm, 'short')
			self.require(self.wait_state_permanence(lambda: valve.get_value() == self.RELAY_OFF
				and reserve_valves.get_value() == self.RELAY_ON,
				self.STABLE_DURATION, self.TRANSITION_TIMEOUT), 'Авария города не перевела ИТП на изолированный резерв')
			self.set_sensor_value(city_alarm, 'open')
			self.set_sensor_value(self.temperature_sensors()[2], self.WARM_SUPPLY)
			self.require(self.wait_state_permanence(lambda: valve.get_value() == self.RELAY_OFF
				and reserve_valves.get_value() == self.RELAY_ON, self.ISOLATION_OBSERVATION),
				'ИТП вернулся на город без диагностического открытия')
			self.require(circuit.write_parameter('generatorId', self.DISCONNECTED_GENERATOR_ID),
				'Не удалось отключить потребителя')
			self.require(self.wait_backup_generator_not_requested(boiler, self.STABLE_DURATION,
				self.TRANSITION_TIMEOUT), 'После снятия запроса потребителя резерв не отключился')
			self.require(self.wait_until(lambda: reserve_valves.get_value() == self.RELAY_OFF,
				self.TRANSITION_TIMEOUT), 'Краны остались открыты после отключения резерва')
			self._status = 'OK'
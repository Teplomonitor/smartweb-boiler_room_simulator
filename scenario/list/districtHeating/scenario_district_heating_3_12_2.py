from consoleLog import print_log
from scenario.base.district_heating_checks import DistrictHeatingChecks
import smartnet.constants as snc
import smartnet.remoteControl as sr


class Scenario(DistrictHeatingChecks):
	ESTIMATED_RUN_SECONDS = 1060
	OUTDOOR_TEMPERATURE_POINT_I = 10
	OUTDOOR_TEMPERATURE_OFFSET = 5
	OUTDOOR_TEMPERATURE_SETTLING_TIMEOUT = 300
	POLL_INTERVAL = 5
	OUTDOOR_TEMPERATURE_TOLERANCE = 1
	BACKWARD_TEMPERATURE_RECALCULATION_WAIT = 10

	def get_scenario_title(self):
		return 'District Heating: outdoor-temperature backward limit'

	def get_scenario_description(self):
		return 'Если Темп. огранич. = Авто, максимально допустимая температура обратки зависит от уличной температуры по двум заданным точкам'

	def get_checklist_id(self):
		return '3.12.2'

	def get_required_programs(self):
		return dict(super().get_required_programs(), weather_consumer=snc.ProgramType.HEATING_CIRCUIT)

	def read_filtered_outdoor_temperature(self, requested_temperature):
		self.set_outdoor_temperature(requested_temperature)
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.CIRCUIT,
			parameterId=snc.CircuitParameterId.OUTDOOR_TEMPERATURE,
			programId=self._programList['weather_consumer'].get_id(),
		)
		observed = None
		def received():
			nonlocal observed
			if not parameter.read():
				return False
			observed = parameter.get_value()
			return self.is_temperature(observed) and abs(observed - requested_temperature) <= self.OUTDOOR_TEMPERATURE_TOLERANCE
		print_log(f'Ждём принятую контроллером температуру улицы {requested_temperature:g} C')
		return observed if self.wait_until(received, self.OUTDOOR_TEMPERATURE_SETTLING_TIMEOUT) else None

	def run(self):
		settings = ((self._district_heating, 'backwardControlType', self.BACKWARD_CONTROL_TYPE_AUTO),)
		with self.conditions((self._outdoor.getOutdoorTemperature(),), settings) as ready:
			if not ready:
				return
			maximum_i = self.read_maximum_backward_temperature()
			maximum_ii = self.read_maximum_backward_temperature_ii()
			outdoor_ii = self.read_outdoor_temperature_ii()
			self.require(all(self.is_temperature(value) for value in (maximum_i, maximum_ii, outdoor_ii)),
				'Не прочитаны точки ограничения обратки')
			outdoor_i = self.OUTDOOR_TEMPERATURE_POINT_I
			self.require(outdoor_ii < outdoor_i, 'Неверный порядок температурных точек')
			distance = outdoor_i - outdoor_ii
			points = (outdoor_ii - self.OUTDOOR_TEMPERATURE_OFFSET, outdoor_ii,
				outdoor_ii + distance / 4, outdoor_ii + distance / 2,
				outdoor_ii + distance * 3 / 4, outdoor_i, outdoor_i + self.OUTDOOR_TEMPERATURE_OFFSET)
			for requested in points:
				actual = self.read_filtered_outdoor_temperature(requested)
				self.require(actual is not None, f'Контроллер не подтвердил улицу {requested:g} C')
				expected = maximum_i if actual > outdoor_i else maximum_ii if actual < outdoor_ii else (
					maximum_i + (actual - outdoor_i) * (maximum_ii - maximum_i) / (outdoor_ii - outdoor_i))
				self.require(self.wait(self.BACKWARD_TEMPERATURE_RECALCULATION_WAIT), 'Проверка прервана')
				current = self.read_current_maximum_backward_temperature()
				print_log(f'Улица {actual:g} C; предел {current}, ожидается {expected:g} C')
				self.require(self.is_temperature(current) and abs(current - expected) <= self.BACKWARD_TEMPERATURE_TOLERANCE,
					'Предел обратки не соответствует принятой уличной температуре')
			self._status = 'OK'
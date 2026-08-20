from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc


class Scenario(DistrictHeatingScenario):
	STARTUP_TIMEOUT = 2 * 60
	STARTUP_STABILIZATION_DURATION = 20
	ALARM_RESPONSE_TIMEOUT = 3 * 60
	ALARM_RESPONSE_STABILIZATION_DURATION = 30
	VALVE_CLOSED_POSITION = 10

	def get_scenario_title(self):
		return 'District Heating: emergency signal switches off pumps and closes valve'

	def get_scenario_description(self):
		return (
			'Если ИТП получает сигнал аварии от программы подпитки при низком давлении, '
			'насосы загрузки и циркуляции выключаются, а кран закрывается'
		)

	def get_checklist_id(self):
		return '3.12.11'

	def get_default_preset(self):
		return 'district_heating_3_12_11'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'outdoor': snc.ProgramType.OUTDOOR_SENSOR,
			'heatingCircuit': snc.ProgramType.HEATING_CIRCUIT,
			'alarm': snc.ProgramType.FILLING_LOOP,
		}

	def valve_is_closed(self, valve):
		value = valve.get_value()
		return value is not None and value <= self.VALVE_CLOSED_POSITION

	def outputs_are_in_emergency_state(self, loading_pump, circulation_pump, valve):
		return (
			loading_pump.get_value() == self.RELAY_OFF
			and circulation_pump.get_value() == self.RELAY_OFF
			and self.valve_is_closed(valve)
		)

	def run(self):
		self._alarm = self._programList['alarm']
		pressure_sensor = self._alarm.getPressure()
		loading_pump = self._district_heating.get_output_channel('supply_pump')
		circulation_pump = self._district_heating.get_output_channel('circulation_pump')
		analog_valve = self._district_heating.get_output_channel('analog_valve')

		if not pressure_sensor.is_mapped():
			print_error('Не найден датчик давления программы подпитки')
			self._status = 'FAIL'
			return

		for channel, description in (
			(loading_pump, 'выход насоса загрузки'),
			(circulation_pump, 'выход циркуляционного насоса'),
			(analog_valve, 'аналоговый выход крана'),
		):
			if not channel.is_mapped():
				print_error(f'Не найден {description}')
				self._status = 'FAIL'
				return

		try:
			print_log(
				f'Ждём исходное рабочее состояние ИТП не более {self.STARTUP_TIMEOUT} секунд'
			)
			if not self.wait_state_permanence(
				lambda: (
					loading_pump.get_value() == self.RELAY_ON
					and circulation_pump.get_value() == self.RELAY_ON
					and not self.valve_is_closed(analog_valve)
				),
				self.STARTUP_STABILIZATION_DURATION,
				self.STARTUP_TIMEOUT,
			):
				print_error('ИТП не перешёл в исходное рабочее состояние')
				self._status = 'FAIL'
				return

			print_log('Подаём сигнал аварии: низкое давление в программе подпитки')
			self.set_sensor_value(pressure_sensor, 'open')

			print_log(
				'Ждём закрытия крана и выключения насосов не более '
				f'{self.ALARM_RESPONSE_TIMEOUT} секунд'
			)
			if not self.wait_state_permanence(
				lambda: self.outputs_are_in_emergency_state(
					loading_pump,
					circulation_pump,
					analog_valve,
				),
				self.ALARM_RESPONSE_STABILIZATION_DURATION,
				self.ALARM_RESPONSE_TIMEOUT,
			):
				print_error(
					'ИТП не выключил оба насоса и не закрыл кран после сигнала аварии: '
					f'насос загрузки={loading_pump.get_value()}, '
					f'циркуляционный насос={circulation_pump.get_value()}, '
					f'кран={analog_valve.get_value()}'
				)
				self._status = 'FAIL'
				return

			print_log('ИТП выключил насосы и закрыл кран по сигналу аварии')
			self._status = 'OK'
		finally:
			self.set_sensor_value(pressure_sensor, 'short')

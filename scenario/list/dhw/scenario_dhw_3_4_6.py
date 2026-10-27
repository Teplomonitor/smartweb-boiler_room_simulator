import smartnet.constants as snc

from consoleLog import print_error, print_log
from scenario.base.filling_loop_alarm import FillingLoopAlarmScenario


class Scenario(FillingLoopAlarmScenario):
	MODE_COMFORT = 0
	CIRCULATION_ON = 0
	COLD_TEMPERATURE = 20
	COMFORT_TEMPERATURE = 60
	PUMP_RELIEF_OFF = 0
	TIMEOUT = 120
	ALARM_DURATION = 5

	def get_scenario_title(self): return 'DHW test 6 - pumps shutdown on alarm'

	def get_scenario_description(self):
		return (
			'ГВС выключает насосы загрузки и циркуляции при аварии от программы '
			'подпитки и возобновляет их работу после нормализации давления'
		)

	def get_checklist_id(self): return '3.4.6'

	def get_default_preset(self):
		return 'dhw'

	def get_required_programs(self):
		return {
			'dhw': snc.ProgramType.DHW,
			'filling_loop': snc.ProgramType.FILLING_LOOP,
		}

	def get_filling_alarm_state(self):
		return self._programList['filling_loop'].get_output_channel('alarm_output').get_value()

	def filling_alarm_is_on(self):
		value = self.get_filling_alarm_state()
		return value is not None and value != self.RELAY_OFF

	def filling_alarm_is_off(self):
		return self.get_filling_alarm_state() == self.RELAY_OFF

	def _pumps_are(self, running):
		expected = self.RELAY_ON if running else self.RELAY_OFF
		return all(pump.get_value() == expected for pump in self._pumps)

	def _check_state(self, alarm, running, description):
		print_log(description)
		if not self.wait_state_permanence(
			lambda: self._alarm_is(alarm) and self._pumps_are(running),
			self.ALARM_DURATION, self.TIMEOUT,
		):
			print_error(f'Не подтверждено состояние: {description}')
			return False
		return True

	def _sequence(self):
		if not self._check_state(False, True, 'Нормальное давление: оба насоса ГВС работают'):
			return False
		self._set_pressure(self.PRESSURE_LOW)
		if not self.wait_event(self.filling_alarm_is_on, self.ALARM_TIMEOUT):
			print_error('Программа подпитки не сформировала аварию')
			return False
		if not self._check_state(True, False, 'Авария подпитки: оба насоса ГВС выключены'):
			return False
		self._set_pressure(self.PRESSURE_NORMAL)
		return self._check_state(False, True, 'Давление восстановлено: оба насоса ГВС снова работают')

	def run(self):
		dhw = self._programList['dhw']
		self._pumps = [dhw.get_supply_pump_state(), dhw.get_circulation_pump_state()]
		settings = [
			(dhw, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.ALARM_PROGRAM_ID,
			 self._programList['filling_loop'].get_id()),
			(dhw, snc.ProgramType.DHW, snc.DhwParameterId.WORK_MODE, self.MODE_COMFORT),
			(dhw, snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT, self.COMFORT_TEMPERATURE),
			(dhw, snc.ProgramType.DHW, snc.DhwParameterId.CIRCULATION_MODE, self.CIRCULATION_ON),
			(dhw, snc.ProgramType.DHW, snc.DhwParameterId.DHW_RELIEF, self.PUMP_RELIEF_OFF),
		]
		sensors = [(dhw.get_temperature(), self.COLD_TEMPERATURE)]
		self._run_alarm_test(settings, sensors, self._pumps, self._sequence)
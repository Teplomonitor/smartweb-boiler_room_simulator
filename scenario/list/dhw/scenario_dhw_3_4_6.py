import smartnet.constants as snc

from consoleLog import print_error, print_log
from scenario.base.dhw import DhwScenario


class Scenario(DhwScenario):
	PRESSURE_NORMAL = 3
	PRESSURE_LOW = 0
	TIMEOUT = 60
	ALARM_DURATION = 5

	def get_scenario_title(self): return 'DHW test 6 - pumps shutdown on alarm'

	def get_scenario_description(self):
		return 'ГВС выключает насосы загрузки и циркуляции при аварии от программы подпитки'

	def get_checklist_id(self): return '3.4.6'

	def get_required_programs(self):
		return {
			'dhw': snc.ProgramType.DHW,
			'filling_loop': snc.ProgramType.FILLING_LOOP,
		}

	def get_filling_alarm_state(self):
		return self._filling_loop.get_output_channel('alarm_output').get_value()

	def filling_alarm_is_on(self):
		return self.get_filling_alarm_state() != self.RELAY_OFF

	def filling_alarm_is_off(self):
		return not self.filling_alarm_is_on()

	def run(self):
		try:
			print_log('устанавливаем нормальное давление подпитки')
			if not self.set_pressure(self.PRESSURE_NORMAL):
				self._status = 'FAIL'
				return
			if not self.wait_event(self.filling_alarm_is_off, self.TIMEOUT):
				print_error('Плохо! авария подпитки не снимается при нормальном давлении')
				self._status = 'FAIL'
				return

			print_log('задаём низкое давление для формирования аварии')
			self.set_pressure(self.PRESSURE_LOW)
			if not self.wait_event(self.filling_alarm_is_on, self.TIMEOUT):
				print_error('Плохо! программа подпитки не сформировала аварию')
				self._status = 'FAIL'
				return

			print_log('проверяем отключение насосов ГВС по аварии')
			if self.wait_state_permanence(self.pumps_are_off, self.ALARM_DURATION, self.TIMEOUT):
				print_log('Хорошо! оба насоса ГВС отключились по аварии')
				self._status = 'OK'
			else:
				print_error('Плохо! насосы ГВС не отключились по аварии')
				self._status = 'FAIL'
		finally:
			self.set_pressure(self.PRESSURE_NORMAL)

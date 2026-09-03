from consoleLog import print_error, print_log
from scenario.base.dhw import DhwScenario


class Scenario(DhwScenario):
	HYSTERESIS_MARGIN = 0.5
	TIMEOUT = 60

	def get_scenario_title(self): return 'DHW test 3 - loading pump temperature control'

	def get_scenario_description(self):
		return 'ГВС включает и выключает насос загрузки по текущей и требуемой температуре'

	def get_checklist_id(self): return '3.4.3'

	def run(self):
		required_temperature = self.read_required_temperature()
		if required_temperature is None:
			print_error('Не удалось получить требуемую температуру ГВС')
			self._status = 'FAIL'
			return

		try:
			print_log('задаём температуру бойлера выше требуемой')
			self.set_boiler_temperature(required_temperature + 2 * self.HYSTERESIS_MARGIN)
			if not self.wait_event(self.supply_pump_is_off, self.TIMEOUT):
				print_error('Плохо! насос загрузки не выключился')
				self._status = 'FAIL'
				return

			print_log('задаём температуру бойлера ниже требуемой')
			self.set_boiler_temperature(required_temperature - 2 * self.HYSTERESIS_MARGIN)
			if not self.wait_event(self.supply_pump_is_on, self.TIMEOUT):
				print_error('Плохо! насос загрузки не включился')
				self._status = 'FAIL'
				return

			print_log('Хорошо! насос загрузки реагирует на температуру бойлера')
			self._status = 'OK'
		finally:
			# Keep the scenario input deterministic for the next test.
			self.set_boiler_temperature(required_temperature)

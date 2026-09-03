from consoleLog import print_error, print_log
from scenario.base.dhw import DhwScenario


class Scenario(DhwScenario):
	TEMPERATURE_TOLERANCE = 0.2
	TIMEOUT = 60

	def get_scenario_title(self): return 'DHW test 1 - boiler temperature input'

	def get_scenario_description(self):
		return 'ГВС видит температуру бойлера косвенного нагрева'

	def get_checklist_id(self): return '3.4.1'

	def run(self):
		test_temperature = 55
		print_log(f'задаём температуру бойлера {test_temperature} °C')
		self.set_boiler_temperature(test_temperature)
		def temperature_matches():
			actual_temperature = self._dhw.get_temperature().get_value()
			return actual_temperature is not None and abs(actual_temperature - test_temperature) <= self.TEMPERATURE_TOLERANCE

		if self.wait_event(
			temperature_matches,
			self.TIMEOUT,
		):
			print_log('Хорошо! ГВС видит температуру бойлера')
			self._status = 'OK'
		else:
			print_error('Плохо! ГВС не видит температуру бойлера')
			self._status = 'FAIL'

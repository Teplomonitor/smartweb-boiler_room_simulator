from consoleLog import print_error, print_log
from scenario.base.filling_loop import FillingLoopScenario


class Scenario(FillingLoopScenario):
	START_TIMEOUT = 30
	STABILIZATION_DURATION = 3

	def get_scenario_title(self):
		return 'Filling loop: automatic filling starts at low pressure'

	def get_scenario_description(self):
		return 'В автоматическом режиме программа подпитки включает реле клапана при низком давлении'

	def get_checklist_id(self):
		return '3.13.1'

	def run(self):
		try:
			if not self.prepare_low_pressure_test():
				print_error('Не удалось подготовить программу подпитки')
				self._status = 'FAIL'
				return

			print_log('Ждём включения реле клапана подпитки')
			if self.wait_state_permanence(
				self.filling_is_on,
				self.STABILIZATION_DURATION,
				self.START_TIMEOUT,
			):
				print_log('Реле клапана подпитки включилось при низком давлении')
				self._status = 'OK'
			else:
				print_error('Реле клапана подпитки не включилось при низком давлении')
				self._status = 'FAIL'
		finally:
			self.finish_test()

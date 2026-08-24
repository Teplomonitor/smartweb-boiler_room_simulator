from consoleLog import print_error, print_log
from scenario.base.filling_loop import FillingLoopScenario


class Scenario(FillingLoopScenario):
	TEST_DURATION = 5
	ALARM_TIMEOUT_MARGIN = 30
	ALARM_STABILIZATION_DURATION = 3

	def get_scenario_title(self):
		return 'Filling loop: alarm after maximum filling duration'

	def get_scenario_description(self):
		return 'При длительной подпитке клапан отключается по заданному времени и включается авария'

	def get_checklist_id(self):
		return '3.13.2'

	def run(self):
		original_duration = self.read_filling_duration()
		if original_duration is None:
			print_error('Не удалось прочитать время подпитки')
			self._status = 'FAIL'
			return

		try:
			if not self.write_parameter('fillingDuration', self.TEST_DURATION):
				print_error('Не удалось установить короткое время подпитки')
				self._status = 'FAIL'
				return
			if not self.prepare_low_pressure_test():
				print_error('Не удалось подготовить программу подпитки')
				self._status = 'FAIL'
				return

			print_log('Ждём включения клапана подпитки')
			if not self.wait_event(self.filling_is_on, 30):
				print_error('Клапан подпитки не включился')
				self._status = 'FAIL'
				return

			print_log('Ждём аварии после истечения времени подпитки')
			if self.wait_state_permanence(
				lambda: self.alarm_is_on() and self.filling_is_off(),
				self.ALARM_STABILIZATION_DURATION,
				self.TEST_DURATION + self.ALARM_TIMEOUT_MARGIN,
			):
				print_log('Клапан отключился, авария включилась')
				self._status = 'OK'
			else:
				print_error('Авария не включилась или клапан не отключился вовремя')
				self._status = 'FAIL'
		finally:
			self.finish_test(original_duration)

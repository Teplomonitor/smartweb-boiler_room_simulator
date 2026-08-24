from consoleLog import print_error, print_log
from scenario.base.filling_loop import FillingLoopScenario


class Scenario(FillingLoopScenario):
	TEST_DURATION = 5
	START_TIMEOUT = 30
	OFF_TIMEOUT_MARGIN = 30

	def get_scenario_title(self):
		return 'Filling loop: single filling runs for configured duration'

	def get_scenario_description(self):
		return 'Однократная подпитка включает реле клапана на заданное время'

	def get_checklist_id(self):
		return '3.13.4'

	def run(self):
		original_duration = self.read_filling_duration()
		if original_duration is None:
			print_error('Не удалось прочитать время подпитки')
			self._status = 'FAIL'
			return

		try:
			if not self.write_parameter('fillingDuration', self.TEST_DURATION):
				print_error('Не удалось установить длительность однократной подпитки')
				self._status = 'FAIL'
				return
			if not self.reset_test_state():
				print_error('Не удалось подготовить программу подпитки')
				self._status = 'FAIL'
				return
			self.set_low_pressure()
			if not self.write_parameter('singleFill', 1):
				print_error('Не удалось включить однократную подпитку')
				self._status = 'FAIL'
				return

			if not self.wait_event(self.filling_is_on, self.START_TIMEOUT):
				print_error('Однократная подпитка не включила реле')
				self._status = 'FAIL'
				return
			self.set_normal_pressure()

			print_log(f'Ждём отключения реле через {self.TEST_DURATION} секунд')
			if self.wait_state_permanence(
				self.filling_is_off,
				2,
				self.TEST_DURATION + self.OFF_TIMEOUT_MARGIN,
			) and self.alarm_is_off():
				print_log('Однократная подпитка завершилась по заданному времени')
				self._status = 'OK'
			else:
				print_error('Однократная подпитка не завершилась корректно')
				self._status = 'FAIL'
		finally:
			self.finish_test(original_duration)

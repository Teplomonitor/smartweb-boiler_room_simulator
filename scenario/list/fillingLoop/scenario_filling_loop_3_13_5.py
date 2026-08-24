from consoleLog import print_error, print_log
from scenario.base.filling_loop import FillingLoopScenario


class Scenario(FillingLoopScenario):
	TEST_DURATION = 5
	ALARM_TIMEOUT = 30
	RESET_TIMEOUT = 30

	def get_scenario_title(self):
		return 'Filling loop: single filling resets the alarm'

	def get_scenario_description(self):
		return 'Однократная подпитка сбрасывает ранее активированную аварию программы подпитки'

	def get_checklist_id(self):
		return '3.13.5'

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
			if not self.wait_event(self.alarm_is_on, self.TEST_DURATION + self.ALARM_TIMEOUT):
				print_error('Не удалось активировать аварию длительной подпиткой')
				self._status = 'FAIL'
				return

			if not self.write_parameter('autoFill', 0):
				print_error('Не удалось отключить автоматический режим')
				self._status = 'FAIL'
				return
			self.wait(2)
			if not self.write_parameter('singleFill', 1):
				print_error('Не удалось включить однократную подпитку')
				self._status = 'FAIL'
				return

			print_log('Проверяем сброс аварии однократной подпиткой')
			if self.wait_state_permanence(
				lambda: self.alarm_is_off() and self.filling_is_on(),
				2,
				self.RESET_TIMEOUT,
			):
				print_log('Однократная подпитка сбросила аварию')
				self._status = 'OK'
			else:
				print_error('Однократная подпитка не сбросила аварию')
				self._status = 'FAIL'
		finally:
			self.finish_test(original_duration)

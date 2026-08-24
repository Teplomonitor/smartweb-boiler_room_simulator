from consoleLog import print_error, print_log
from scenario.base.filling_loop import FillingLoopScenario


class Scenario(FillingLoopScenario):
	TEST_DURATION = 5
	ALARM_TIMEOUT = 30
	RESET_TIMEOUT = 30

	def get_scenario_title(self):
		return 'Filling loop: remote alarm reset command'

	def get_scenario_description(self):
		return 'Команда PRESSURE_LOSS_ALARM_RESET = 0 снимает аварию программы подпитки'

	def get_checklist_id(self):
		return '3.13.6'

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

			print_log('Передаём PRESSURE_LOSS_ALARM_RESET = 0')
			if not self.write_parameter('pressureLossAlarmReset', 0):
				print_error('Не удалось записать сброс аварии')
				self._status = 'FAIL'
				return

			if self.wait_state_permanence(self.alarm_is_off, 2, self.RESET_TIMEOUT):
				print_log('Команда сброса сняла аварию')
				self._status = 'OK'
			else:
				print_error('Команда сброса не сняла аварию')
				self._status = 'FAIL'
		finally:
			self.finish_test(original_duration)

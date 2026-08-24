from consoleLog import print_error, print_log
from scenario.base.filling_loop import FillingLoopScenario


class Scenario(FillingLoopScenario):
	PULSE_TIMEOUT = 30
	STABILIZATION_DURATION = 2
	PULSES_TO_ALARM = 3

	def get_scenario_title(self):
		return 'Filling loop: repeated automatic fillings trigger alarm'

	def get_scenario_description(self):
		return 'Три последовательные автоматические подпитки включают аварию, четвёртая подпитка не включается'

	def get_checklist_id(self):
		return '3.13.3'

	def run(self):
		try:
			if not self.prepare_low_pressure_test():
				print_error('Не удалось подготовить программу подпитки')
				self._status = 'FAIL'
				return

			for pulse_number in range(1, self.PULSES_TO_ALARM + 1):
				print_log(f'Проверяем автоматическую подпитку {pulse_number}')
				if not self.wait_state_permanence(
					self.filling_is_on,
					self.STABILIZATION_DURATION,
					self.PULSE_TIMEOUT,
				):
					print_error(f'Автоматическая подпитка {pulse_number} не включилась')
					self._status = 'FAIL'
					return

				self.set_normal_pressure()
				if not self.wait_state_permanence(
					self.filling_is_off,
					self.STABILIZATION_DURATION,
					self.PULSE_TIMEOUT,
				):
					print_error(f'Автоматическая подпитка {pulse_number} не завершилась')
					self._status = 'FAIL'
					return
				if pulse_number < self.PULSES_TO_ALARM:
					self.set_low_pressure()

			if not self.alarm_is_on():
				print_error('После третьей автоматической подпитки авария не включилась')
				self._status = 'FAIL'
				return

			print_log('Проверяем, что четвёртая автоматическая подпитка заблокирована')
			self.set_low_pressure()
			if self.wait_event(self.filling_is_on, self.PULSE_TIMEOUT):
				print_error('Четвёртая автоматическая подпитка включилась после аварии')
				self._status = 'FAIL'
			else:
				print_log('Четвёртая автоматическая подпитка не включилась')
				self._status = 'OK'
		finally:
			self.finish_test()

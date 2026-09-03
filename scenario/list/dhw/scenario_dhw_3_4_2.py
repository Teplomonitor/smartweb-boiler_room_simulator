from consoleLog import print_error, print_log
from scenario.base.dhw import DhwScenario


class Scenario(DhwScenario):
	TIMEOUT = 60
	CHECK_DURATION = 3
	PERIOD_ON = 2 * 1000
	PERIOD_OFF = 2 * 1000

	def get_scenario_title(self): return 'DHW test 2 - circulation pump modes'

	def get_scenario_description(self):
		return 'ГВС управляет насосом циркуляции в зависимости от заданной программы'

	def get_checklist_id(self): return '3.4.2'

	def run(self):
		original_mode = self.read_parameter('circulationMode')
		original_on = self.read_parameter('circulationPeriodOn')
		original_off = self.read_parameter('circulationPeriodOff')
		try:
			if None in (original_mode, original_on, original_off):
				print_error('Не удалось прочитать параметры насоса циркуляции')
				self._status = 'FAIL'
				return

			checks = [
				(self.CIRCULATION_ON, self.circulation_pump_is_on, 'ON'),
				(self.CIRCULATION_OFF, self.circulation_pump_is_off, 'OFF'),
			]
			for mode, predicate, title in checks:
				print_log(f'проверяем режим циркуляции {title}')
				if self.set_circulation_mode(mode) is None or not self.wait_state_permanence(predicate, self.CHECK_DURATION, self.TIMEOUT):
					print_error(f'Плохо! режим циркуляции {title} работает неверно')
					self._status = 'FAIL'
					return

			if self.write_parameter('circulationPeriodOn', self.PERIOD_ON) is None:
				self._status = 'FAIL'
				return
			if self.write_parameter('circulationPeriodOff', self.PERIOD_OFF) is None:
				self._status = 'FAIL'
				return
			if self.set_circulation_mode(self.CIRCULATION_PERIOD) is None:
				self._status = 'FAIL'
				return

			print_log('Хорошо! насос циркуляции управляется заданными режимами')
			self._status = 'OK'
		finally:
			if original_on is not None:
				self.write_parameter('circulationPeriodOn', original_on)
			if original_off is not None:
				self.write_parameter('circulationPeriodOff', original_off)
			if original_mode is not None:
				self.write_parameter('circulationMode', original_mode)

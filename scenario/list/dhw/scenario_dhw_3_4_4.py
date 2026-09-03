from consoleLog import print_error, print_log
from scenario.base.dhw import DhwScenario


class Scenario(DhwScenario):
	TEMPERATURE_TOLERANCE = 0.2
	TIMEOUT = 60
	TEST_COMFORT = 60
	TEST_ECONOM = 45

	def get_scenario_title(self): return 'DHW test 4 - required temperature by work mode'

	def get_scenario_description(self):
		return 'Требуемая температура ГВС рассчитывается в зависимости от текущего режима работы'

	def get_checklist_id(self): return '3.4.4'

	def temperature_is(self, expected):
		actual = self.read_required_temperature()
		return actual is not None and abs(actual - expected) <= self.TEMPERATURE_TOLERANCE

	def run(self):
		original_mode = self.read_parameter('workMode')
		original_comfort = self.read_parameter('temperatureComfort')
		original_econom = self.read_parameter('temperatureEconom')
		try:
			if None in (original_mode, original_comfort, original_econom):
				print_error('Не удалось прочитать параметры режима и уставок ГВС')
				self._status = 'FAIL'
				return

			if self.write_parameter('temperatureComfort', self.TEST_COMFORT) is None or self.write_parameter('temperatureEconom', self.TEST_ECONOM) is None:
				print_error('Не удалось задать тестовые уставки ГВС')
				self._status = 'FAIL'
				return

			checks = [
				(self.MODE_COMFORT, self.TEST_COMFORT, 'COMFORT'),
				(self.MODE_ECONOM, self.TEST_ECONOM, 'ECONOM'),
				(self.MODE_OFF, 0, 'OFF'),
			]
			for mode, expected, title in checks:
				print_log(f'проверяем режим {title}')
				if self.write_parameter('workMode', mode) is None or not self.wait_event(lambda: self.temperature_is(expected), self.TIMEOUT):
					print_error(f'Плохо! требуемая температура в режиме {title} неверна')
					self._status = 'FAIL'
					return

			print_log('Хорошо! требуемая температура зависит от режима работы')
			self._status = 'OK'
		finally:
			if original_comfort is not None:
				self.write_parameter('temperatureComfort', original_comfort)
			if original_econom is not None:
				self.write_parameter('temperatureEconom', original_econom)
			if original_mode is not None:
				self.write_parameter('workMode', original_mode)

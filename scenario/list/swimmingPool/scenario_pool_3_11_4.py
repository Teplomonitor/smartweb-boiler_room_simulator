'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.swimming_pool import PoolScenario


class Scenario(PoolScenario):
	MODE_COMFORT = 0
	MODE_ECONOM = 1
	MODE_OFF = 3

	TEST_COMFORT_TEMPERATURE = 28
	TEST_ECONOM_TEMPERATURE = 20
	TEMPERATURE_TOLERANCE = 0.1

	def get_scenario_title(self): return 'pool test 4 - required temperature depends on work mode'

	def get_scenario_description(self):
		return 'Проверка расчёта требуемой температуры бассейна в зависимости от режима работы'

	def get_checklist_id(self): return '3.11.4'

	def read_work_mode(self):
		return self._pool.read_parameter_value('workMode')

	def set_work_mode(self, mode):
		return self._pool.write_parameter_value('workMode', mode)

	def read_comfort_temperature(self):
		return self._pool.read_parameter_value('requiredPoolTemperatureComfort')

	def set_comfort_temperature(self, value):
		return self._pool.write_parameter_value('requiredPoolTemperatureComfort', value)

	def read_econom_temperature(self):
		return self._pool.read_parameter_value('requiredPoolTemperatureEconom')

	def set_econom_temperature(self, value):
		return self._pool.write_parameter_value('requiredPoolTemperatureEconom', value)

	def read_current_required_temperature(self):
		return self._pool.read_parameter_value('currentRequiredPoolTemperature')

	def temperatures_equal(self, actual, expected):
		return actual is not None and abs(actual - expected) <= self.TEMPERATURE_TOLERANCE

	def check_mode_temperature(self, mode, expected_temperature, mode_title):
		print_log(f'устанавливаем режим {mode_title}')
		if self.set_work_mode(mode) is None:
			print_error(f'Плохо, не удалось установить режим {mode_title}')
			return False

		print_log(f'проверяем требуемую температуру в режиме {mode_title}')
		if self.wait_event(
			lambda: self.temperatures_equal(
				self.read_current_required_temperature(), expected_temperature
			),
			15
		):
			print_log(
				f'Хорошо, в режиме {mode_title} требуемая температура '
				f'равна {expected_temperature}'
			)
			return True

		actual_temperature = self.read_current_required_temperature()
		print_error(
			f'Плохо, в режиме {mode_title} требуемая температура '
			f'равна {actual_temperature}, ожидалось {expected_temperature}'
		)
		return False

	def run(self):
		original_mode = self.read_work_mode()
		original_comfort_temperature = self.read_comfort_temperature()
		original_econom_temperature = self.read_econom_temperature()

		try:
			if original_mode is None:
				self._status = 'FAIL'
				print_error('Проблема! не удалось получить текущий режим бассейна')
				return

			if original_comfort_temperature is None or original_econom_temperature is None:
				self._status = 'FAIL'
				print_error('Проблема! не удалось получить уставки бассейна')
				return

			print_log(
				f'временно задаём комфортную уставку {self.TEST_COMFORT_TEMPERATURE} '
				f'и экономичную уставку {self.TEST_ECONOM_TEMPERATURE}'
			)
			if self.set_comfort_temperature(self.TEST_COMFORT_TEMPERATURE) is None:
				self._status = 'FAIL'
				print_error('Плохо, не удалось задать комфортную уставку')
				return

			if self.set_econom_temperature(self.TEST_ECONOM_TEMPERATURE) is None:
				self._status = 'FAIL'
				print_error('Плохо, не удалось задать экономичную уставку')
				return

			checks = [
				(self.MODE_COMFORT, self.TEST_COMFORT_TEMPERATURE, 'COMFORT'),
				(self.MODE_ECONOM, self.TEST_ECONOM_TEMPERATURE, 'ECONOM'),
				(self.MODE_OFF, 0, 'OFF'),
			]

			for mode, expected_temperature, mode_title in checks:
				if not self.check_mode_temperature(mode, expected_temperature, mode_title):
					self._status = 'FAIL'
					return

			self._status = 'OK'
			print_log('Хорошо! Требуемая температура зависит от режима работы бассейна')
		finally:
			print_log('восстанавливаем исходные настройки бассейна')
			if original_comfort_temperature is not None:
				self.set_comfort_temperature(original_comfort_temperature)
			if original_econom_temperature is not None:
				self.set_econom_temperature(original_econom_temperature)
			if original_mode is not None:
				self.set_work_mode(original_mode)
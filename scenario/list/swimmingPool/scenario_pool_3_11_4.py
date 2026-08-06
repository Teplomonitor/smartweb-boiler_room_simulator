'''
@author: admin
'''

import datetime

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.swimming_pool import PoolScenario


class Scenario(PoolScenario):
	MODE_COMFORT = 0
	MODE_ECONOM = 1
	MODE_PROGRAM = 2
	MODE_OFF = 3

	TEST_COMFORT_TEMPERATURE = 28
	TEST_ECONOM_TEMPERATURE = 20
	TEMPERATURE_TOLERANCE = 0.1
	TEST_DATE = datetime.date(2026, 8, 3)
	TEST_NEXT_DATE = TEST_DATE + datetime.timedelta(days=1)
	TEST_DAY_PERIOD = 0
	TEST_NEXT_DAY_PERIOD = 0
	EMPTY_SCHEDULE = (0, 0, 0, 0)
	TEST_DAY_SCHEDULE = (18, 0, 24, 0)
	TEST_NEXT_DAY_SCHEDULE = (0, 0, 6, 0)

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

	def read_schedule(self, weekday, period):
		return self._pool.read_parameter_value('schedule', index=(weekday, period))

	def set_schedule(self, weekday, period, value):
		return self._pool.write_parameter_value(
			'schedule', value, index=(weekday, period)
		)

	def read_controller_date(self):
		return self._controllerHost.read_date()

	def set_controller_date(self, value):
		return self._controllerHost.write_date(value)

	def read_controller_time(self):
		return self._controllerHost.read_time()

	def set_controller_time(self, value):
		return self._controllerHost.write_time(value)

	def date_value(self, value):
		return (value.day, value.weekday(), value.month, value.year)

	def set_controller_clock(self, date_value, hour, minute):
		if not self.set_controller_date(self.date_value(date_value)):
			return False
		return self.set_controller_time((hour, minute, 0, 0))

	def configure_test_schedule(self, weekday, period):
		for schedule_period in range(3):
			value = self.EMPTY_SCHEDULE
			if schedule_period == period:
				value = self.TEST_DAY_SCHEDULE
			if self.set_schedule(weekday, schedule_period, value) is None:
				return False
		return True

	def configure_next_day_schedule(self, weekday, period):
		for schedule_period in range(3):
			value = self.EMPTY_SCHEDULE
			if schedule_period == period:
				value = self.TEST_NEXT_DAY_SCHEDULE
			if self.set_schedule(weekday, schedule_period, value) is None:
				return False
		return True

	def check_program_temperature(self, expected_temperature, title):
		print_log(f'проверяем требуемую температуру в режиме PROGRAM ({title})')
		if self.wait_event(
			lambda: self.temperatures_equal(
				self.read_current_required_temperature(), expected_temperature
			),
			15
		):
			print_log(
				f'Хорошо, в режиме PROGRAM ({title}) требуемая температура '
				f'равна {expected_temperature}'
			)
			return True

		actual_temperature = self.read_current_required_temperature()
		print_error(
			f'Плохо, в режиме PROGRAM ({title}) требуемая температура '
			f'равна {actual_temperature}, ожидалось {expected_temperature}'
		)
		return False

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
		original_date = self.read_controller_date()
		original_time = self.read_controller_time()
		test_schedule_selectors = [
			(self.TEST_DATE.weekday(), self.TEST_DAY_PERIOD),
			(self.TEST_DATE.weekday(), 1),
			(self.TEST_DATE.weekday(), 2),
			(self.TEST_NEXT_DATE.weekday(), self.TEST_NEXT_DAY_PERIOD),
			(self.TEST_NEXT_DATE.weekday(), 1),
			(self.TEST_NEXT_DATE.weekday(), 2),
		]
		original_schedules = {
			selector: self.read_schedule(*selector)
			for selector in test_schedule_selectors
		}

		try:
			if original_mode is None:
				self._status = 'FAIL'
				print_error('Проблема! не удалось получить текущий режим бассейна')
				return

			if original_comfort_temperature is None or original_econom_temperature is None:
				self._status = 'FAIL'
				print_error('Проблема! не удалось получить уставки бассейна')
				return

			if original_date is None or original_time is None:
				self._status = 'FAIL'
				print_error('Проблема! не удалось получить дату и время контроллера')
				return

			if any(value is None for value in original_schedules.values()):
				self._status = 'FAIL'
				print_error('Проблема! не удалось получить расписание бассейна')
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

			print_log('настраиваем расписание бассейна с переходом через полночь')
			if not self.configure_test_schedule(
				self.TEST_DATE.weekday(), self.TEST_DAY_PERIOD
			) or not self.configure_next_day_schedule(
				self.TEST_NEXT_DATE.weekday(), self.TEST_NEXT_DAY_PERIOD
			):
				self._status = 'FAIL'
				print_error('Плохо, не удалось задать расписание бассейна')
				return

			if not self.check_mode_temperature(self.MODE_PROGRAM, self.TEST_COMFORT_TEMPERATURE, 'PROGRAM'):
				self._status = 'FAIL'
				return

			print_log('проверяем комфортную уставку до полуночи')
			if not self.set_controller_clock(self.TEST_DATE, 23, 59):
				self._status = 'FAIL'
				print_error('Плохо, не удалось установить время до полуночи')
				return
			if not self.check_program_temperature(self.TEST_COMFORT_TEMPERATURE, 'до полуночи'):
				self._status = 'FAIL'
				return

			print_log('проверяем комфортную уставку после полуночи')
			if not self.set_controller_clock(self.TEST_NEXT_DATE, 0, 1):
				self._status = 'FAIL'
				print_error('Плохо, не удалось установить время после полуночи')
				return
			if not self.check_program_temperature(self.TEST_COMFORT_TEMPERATURE, 'после полуночи'):
				self._status = 'FAIL'
				return

			print_log('проверяем экономичную уставку вне периода расписания')
			if not self.set_controller_time((12, 0, 0, 0)):
				self._status = 'FAIL'
				print_error('Плохо, не удалось установить время вне расписания')
				return
			if not self.check_program_temperature(self.TEST_ECONOM_TEMPERATURE, 'вне расписания'):
				self._status = 'FAIL'
				return

			self._status = 'OK'
			print_log('Хорошо! Требуемая температура зависит от режима и расписания бассейна')
		finally:
			print_log('восстанавливаем исходные настройки бассейна')
			for selector, value in original_schedules.items():
				if value is not None:
					self.set_schedule(*selector, value)
			if original_comfort_temperature is not None:
				self.set_comfort_temperature(original_comfort_temperature)
			if original_econom_temperature is not None:
				self.set_econom_temperature(original_econom_temperature)
			if original_mode is not None:
				self.set_work_mode(original_mode)
			if original_date is not None:
				self.set_controller_date(original_date)
			if original_time is not None:
				self.set_controller_time(original_time)
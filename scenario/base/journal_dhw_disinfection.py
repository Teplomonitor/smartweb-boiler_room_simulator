import datetime
import time

from consoleLog import print_error
from scenario.base.journal import JournalScenarioMixin
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
import smartnet.remoteControl as sr


class JournalDhwDisinfectionScenario(JournalScenarioMixin, Parent):
	TEST_SUNDAY_TIME = (23, 58, 0, 0)
	START_TIMEOUT = 180
	END_TIMEOUT = 65 * 60

	def get_required_programs(self):
		return {'dhw': snc.ProgramType.DHW}

	def get_default_preset(self):
		return 'boiler_3_5_2'

	def force_preset_load(self):
		return True

	def _write_antilegion(self, value):
		return sr.RemoteControlParameter(
			programType=snc.ProgramType.DHW,
			parameterId=snc.DhwParameterId.ANTILEGION,
			parameterValue=value,
			programId=self._programList['dhw'].get_id(),
		).write()

	def prepare_disinfection(self):
		self._original_antilegion = None
		self._original_clock = None
		self._clock_changed = False
		controller = self._controllerHost
		clock_start = time.monotonic()
		original_date = controller.read_date()
		original_time = controller.read_time()
		if original_date is None or original_time is None:
			print_error('Не удалось прочитать часы контроллера')
			return False
		try:
			day, weekday, month, year = original_date
			hour, minute, second, is_dst = original_time
			original_datetime = datetime.datetime(year, month, day, hour, minute, second)
		except (ValueError, TypeError):
			print_error('Некорректная исходная дата/время контроллера')
			return False

		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.DHW,
			parameterId=snc.DhwParameterId.ANTILEGION,
			programId=self._programList['dhw'].get_id(),
		)
		if not parameter.read() or parameter.get_value() is None:
			print_error('Не удалось прочитать настройку дезинфекции ГВС')
			return False
		self._original_antilegion = parameter.get_value()
		self._original_clock = (original_datetime, is_dst, clock_start)

		# Keep the test journal entries in the past relative to the original RTC.
		days_since_sunday = (original_datetime.weekday() + 1) % 7 or 7
		if original_datetime.weekday() == 0 and original_datetime.time() < datetime.time(1, 10):
			days_since_sunday += 7
		test_date = (original_datetime - datetime.timedelta(days=days_since_sunday)).date()
		self._clock_changed = True
		if not controller.write_date((test_date.day, test_date.weekday(), test_date.month, test_date.year)):
			print_error('Не удалось установить воскресенье на контроллере')
			return False
		if not controller.write_time(self.TEST_SUNDAY_TIME):
			print_error('Не удалось установить время перед понедельником')
			return False
		self.wait(2)
		if not self._write_antilegion(1):
			print_error('Не удалось включить режим Антилегионеллы')
			return False
		return self.snapshot_journal()

	def finish_disinfection(self):
		if self._original_antilegion is None:
			return
		# Disable the service loop while restoring a possibly Monday clock.
		if not self._write_antilegion(0):
			print_error('Не удалось выключить режим Антилегионеллы для восстановления часов')
			self._status = 'FAIL'
		if self._clock_changed and self._original_clock is not None:
			original_datetime, is_dst, clock_start = self._original_clock
			restored = original_datetime + datetime.timedelta(seconds=round(time.monotonic() - clock_start))
			controller = self._controllerHost
			if not controller.write_date((restored.day, restored.weekday(), restored.month, restored.year)):
				print_error('Не удалось восстановить дату контроллера')
				self._status = 'FAIL'
			if not controller.write_time((restored.hour, restored.minute, restored.second, is_dst)):
				print_error('Не удалось восстановить время контроллера')
				self._status = 'FAIL'
		if not self._write_antilegion(self._original_antilegion):
			print_error('Не удалось восстановить исходную настройку дезинфекции ГВС')
			self._status = 'FAIL'
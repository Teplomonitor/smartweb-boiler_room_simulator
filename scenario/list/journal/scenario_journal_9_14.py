from consoleLog import print_error, print_log
from scenario.base.journal_controller import JournalControllerScenario
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalControllerScenario):
	ESTIMATED_RUN_SECONDS = 390

	def get_scenario_title(self):
		return 'Journal: controller connection lost'

	def get_scenario_description(self):
		return 'Нет связи с контроллером <N>: более 5 минут без сообщений от отдельного CAN-контроллера'

	def get_checklist_id(self):
		return '9.14'

	def get_required_programs(self):
		return {}

	def get_default_preset(self):
		return None

	def run(self):
		self._status = 'FAIL'
		original_monitoring = None
		restore_monitoring = False
		emitter = None
		try:
			original_monitoring = self._controllerHost.read_monitoring_enabled()
			if original_monitoring is None:
				print_error('Не удалось прочитать состояние мониторинга по CAN')
				return
			if not original_monitoring:
				# A missing acknowledgement does not mean the write was not applied.
				restore_monitoring = True
				if not self._controllerHost.write_monitoring_enabled(1):
					print_error('Не удалось включить мониторинг по CAN')
					return
			controller_id = self.find_unused_controller_id()
			if controller_id is None or not self.snapshot_journal():
				return
			emitter = self.make_presence_emitter(controller_id)
			emitter.start()
			self.wait(self.ANNOUNCEMENT_SECONDS)
			emitter.stop()
			emitter = None
			print_log(f'Контроллер {controller_id} перестал передавать I_AM_HERE; ожидание потери связи')
			# Do not answer discovery or monitoring requests from this ID.
			self.wait(self.CONNECTION_LOSS_SECONDS)
			if self.wait_journal_entry(
				MessageLogCode.MLC_CONTROLLER_CONNECTION_ERROR,
				SeverityCode.SC_ERROR,
				controller_id,
				self.JOURNAL_TIMEOUT,
			):
				self._status = 'OK'
		finally:
			try:
				if emitter is not None:
					emitter.stop()
			finally:
				if restore_monitoring:
					self._status = 'FAIL' if not self.restore_monitoring(original_monitoring) else self._status

	def restore_monitoring(self, value):
		try:
			if self._controllerHost.write_monitoring_enabled(value):
				return True
		except Exception as exc:
			print_error(f'Ошибка восстановления мониторинга: {exc!r}')
		print_error('Не удалось восстановить исходное состояние мониторинга')
		return False

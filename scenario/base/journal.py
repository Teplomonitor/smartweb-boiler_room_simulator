import time
import threading

from consoleLog import print_error
from scenario.base.filling_loop import FillingLoopScenario
from smartnet.message import CanListener
from smartnet.message_log import MLCDataParser, MessageLogReader, OP_STATUS


class ScenarioJournalReader(MessageLogReader):
	"""Observe end-of-journal without reinterpreting legacy STATUS bytes."""

	def __init__(self, *args, **kwargs):
		self.status_received = False
		super().__init__(*args, **kwargs)

	def on_can_message_received(self, msg):
		with self._capture_lock:
			response_filter = self._response_filter
		if msg is not None and response_filter is not None and msg.compare(response_filter):
			data = msg.get_data()
			if data and len(data) == 8 and MLCDataParser.parse_operation(data[0]) == OP_STATUS:
				self.status_received = True
		super().on_can_message_received(msg)


class JournalCanEmitter:
	def __init__(self, messages, interval=1):
		self._messages = messages
		self._interval = interval
		self._stop_event = threading.Event()
		self._thread = threading.Thread(target=self._run, name='Journal CAN source', daemon=True)

	def _run(self):
		while not self._stop_event.is_set():
			for message in self._messages:
				if self._stop_event.is_set():
					return
				message.send()
			self._stop_event.wait(self._interval)

	def start(self):
		self._thread.start()

	def stop(self):
		self._stop_event.set()
		self._thread.join(timeout=2)


class JournalScenarioMixin:
	JOURNAL_READ_TIMEOUT = 3
	JOURNAL_MAX_ENTRIES = 100
	JOURNAL_POLL_INTERVAL = 1

	def _read_journal(self, cursor):
		reader = ScenarioJournalReader(
			controller_id=self._controllerHost.get_controller_id(),
			timeout=self.JOURNAL_READ_TIMEOUT,
		)
		try:
			entries = reader.read_entries(max_entries=self.JOURNAL_MAX_ENTRIES, last_entry=cursor)
			return entries if reader.status_received else None
		finally:
			CanListener.unsubscribe(reader)

	def snapshot_journal(self):
		"""Remember the newest entry before changing controller inputs."""
		entries = self._read_journal(None)
		if entries is None:
			print_error('Не удалось получить полное исходное состояние журнала по CAN')
			return False
		self._journal_cursor = entries[-1] if entries else None
		return True

	def wait_journal_entry(self, code, severity, program_id, timeout, param_ex=None):
		"""Find an entry created after snapshot_journal, not an old matching alarm."""
		deadline = time.monotonic() + timeout
		while True:
			entries = self._read_journal(self._journal_cursor)
			if entries is None:
				print_error('Чтение журнала по CAN не завершилось')
				return False
			if entries:
				self._journal_cursor = entries[-1]
			for entry in entries:
				if (entry.code == code and entry.severity == severity
						and entry.param == program_id
						and (param_ex is None or bytes(entry.param_ex[:len(param_ex)]) == bytes(param_ex))):
					return True
			if time.monotonic() >= deadline:
				print_error(f'В журнале нет новой записи: код={code}, важность={severity}, программа={program_id}')
				return False
			self.wait(min(self.JOURNAL_POLL_INTERVAL, max(0, deadline - time.monotonic())))


class JournalFillingLoopScenario(JournalScenarioMixin, FillingLoopScenario):
	SHORT_ALARM_DURATION = 5
	ALARM_TIMEOUT_MARGIN = 30
	EVENT_TIMEOUT = 30

	def prepare_journal_test(self, short_alarm=False):
		self._original_duration = self.read_filling_duration()
		if self._original_duration is None:
			print_error('Не удалось прочитать время подпитки')
			return False
		if short_alarm and not self.write_parameter('fillingDuration', self.SHORT_ALARM_DURATION):
			return False
		return self.prepare_pressure_input_type() and self.reset_test_state()

	def finish_journal_test(self):
		self.finish_test(getattr(self, '_original_duration', None))
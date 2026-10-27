"""Shared capture of consumer priority broadcast requests."""

import threading
import time

import smartnet.constants as snc
import smartnet.message as sm


class ConsumerPriorityCapture:
	CAN_BROADCAST_ID = 0

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._priority_lock = threading.Lock()
		self._priority_events = []
		self._priority_listener_active = False

	def _get_priority_program(self):
		raise NotImplementedError

	def _clear_priority_events(self):
		with self._priority_lock:
			self._priority_events.clear()

	def _begin_priority_capture(self):
		self._clear_priority_events()
		sm.CanListener.subscribe(self)
		self._priority_listener_active = True

	def _end_priority_capture(self):
		if self._priority_listener_active:
			sm.CanListener.unsubscribe(self)
			self._priority_listener_active = False

	def on_can_message_received(self, message):
		if (message.get_program_type() != snc.ProgramType.CONSUMER
				or message.getProgramId() != self.CAN_BROADCAST_ID
				or message.getRequestFlag() != snc.RequestFlag.REQUEST):
			return
		if message.getFunctionId() not in (
			snc.ConsumerFunction['GIVE_WAY'], snc.ConsumerFunction['PROCEED'],
		):
			return
		data = message.get_data()
		if data is None or len(data) < 3 or data[0] != self._get_priority_program().get_id():
			return
		with self._priority_lock:
			self._priority_events.append((time.monotonic(), message.getFunctionId(), tuple(data)))

	def _has_priority_event(self, function):
		with self._priority_lock:
			return any(event[1] == function for event in self._priority_events)

	def _priority_event_index(self, function):
		with self._priority_lock:
			return next((i for i, event in enumerate(self._priority_events)
				if event[1] == function), None)

	def _wait_for_message(self, function, timeout):
		return self.wait_event(lambda: self._has_priority_event(function), timeout)
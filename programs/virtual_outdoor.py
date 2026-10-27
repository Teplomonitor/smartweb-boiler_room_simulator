"""A preset-owned outdoor source; no controller program is created for it."""

import threading
import time

from programs.oat import Oat
import smartnet.constants as snc
from smartnet.message import CanBusInterface
from smartnet.outdoor import GET_TEMPERATURE, REPORT_INTERVAL, make_temperature_message
from smartnet.channelMapping import ChannelMapping


class VirtualOutdoor(Oat):
	def __init__(self, preset):
		self._publish_lock = threading.RLock()
		self._closed = False
		self._publish_error = None
		self._last_payload = None
		self._next_report = 0
		super().__init__(preset)
		# A local channel remains visible to the GUI without a hardware sensor.
		self.getOutdoorTemperature().set_mapping(ChannelMapping(0, 'CHANNEL_INPUT', self.get_id()))
		self.getOutdoorTemperature().set_value(-10)

	def publish_temperature(self, force=False):
		with self._publish_lock:
			if self._closed:
				return
			if self._publish_error:
				raise RuntimeError(self._publish_error)
			sensor = self.getOutdoorTemperature()
			state = 'short' if sensor.isShort() else 'open' if sensor.isOpen() else 'normal'
			if sensor.get_value() is None and state == 'normal':
				state = 'undefined'
			message = make_temperature_message(self.get_id(), sensor.get_value(), state)
			now = time.monotonic()
			payload = bytes(message.get_data())
			if force or payload != self._last_payload or now >= self._next_report:
				# Unlike Message.send(), a failed publication must not look successful.
				CanBusInterface().get().send(message.smartNetToCanMsg(), timeout=1.0)
				self._last_payload = payload
				self._next_report = now + REPORT_INTERVAL

	def on_can_message_received(self, message):
		if (message.get_program_type() != snc.ProgramType.OUTDOOR_SENSOR
			or message.getFunctionId() != GET_TEMPERATURE):
			return
		with self._publish_lock:
			if self._closed:
				return
			if (message.getRequestFlag() == snc.RequestFlag.RESPONSE
				and message.getProgramId() != self.get_id()):
				self._publish_error = f'Competing outdoor source detected: {message.getProgramId()}'
			elif (message.getRequestFlag() == snc.RequestFlag.REQUEST
				and message.getProgramId() in (0, self.get_id())):
				try:
					self.publish_temperature(force=True)
				except Exception as error:
					# Report on the simulator thread, never kill the CAN listener.
					self._publish_error = f'Virtual outdoor publication failed: {error}'

	def clear(self):
		with self._publish_lock:
			self._closed = True
			super().clear()
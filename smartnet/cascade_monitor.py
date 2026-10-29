"""Passive CAN observations; never synthesizes controller commands or replies."""

from collections import deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic

import smartnet.constants as snc
from smartnet.message import CanListener


@dataclass(frozen=True)
class PowerCommand:
	time: float
	boiler_id: int
	power: int
	temperature: float


@dataclass(frozen=True)
class OutputReport:
	time: float
	boiler_id: int
	index: int
	value: int


class CascadeMonitor:
	HISTORY_SIZE = 8192

	def __init__(self, cascade_id, boiler_ids, clock=monotonic):
		self.cascade_id = cascade_id
		self.boiler_ids = set(boiler_ids)
		self.clock = clock
		self.lock = Lock()
		self.commands = deque(maxlen=self.HISTORY_SIZE)
		self.outputs = deque(maxlen=self.HISTORY_SIZE)
		self.properties = {}
		self.error = None
		self.command_error = None

	def __enter__(self):
		CanListener.subscribe(self)
		return self

	def __exit__(self, *args):
		CanListener.unsubscribe(self)

	def on_can_message_received(self, message):
		boiler_id = message.getProgramId()
		if boiler_id not in self.boiler_ids:
			return
		data = message.get_data()
		function = message.getFunctionId()
		with self.lock:
			if (message.get_program_type() == snc.ProgramType.REMOTE_CONTROL
				and function == snc.RemoteControlFunction.GET_PARAMETER_VALUE
				and message.getRequestFlag() == snc.RequestFlag.RESPONSE
				and data is not None and len(data) >= 2
				and data[0] == snc.ProgramType.PROGRAM
				and data[1] == snc.ProgramParameterId.OUTPUT):
				if len(data) not in (4, 8) or any(data[4:]):
					self.error = f'Invalid boiler output report for {boiler_id}: {data}'
					return
				if len(self.outputs) == self.HISTORY_SIZE:
					self.error = 'Boiler output history overflow'
				self.outputs.append(OutputReport(self.clock(), boiler_id, data[2], data[3]))
				return
			if message.get_program_type() != snc.ProgramType.TEMPERATURE_SOURCE:
				return
			if (function == snc.TemperatureSourceFunction['REQUEST_POWER']
				and message.getRequestFlag() == snc.RequestFlag.REQUEST):
				# REQUEST_POWER: uint8 power, int16 temperature (0.1 C), uint8 consumer.
				if data is None or len(data) not in (4, 8) or any(data[4:]):
					self.command_error = f'Invalid REQUEST_POWER for boiler {boiler_id}: {data}'
					return
				if data[3] != self.cascade_id:
					self.command_error = f'Unexpected power requester {data[3]} for boiler {boiler_id}'
					return
				if data[0] > 100:
					self.command_error = f'Invalid boiler power: {data[0]}'
					return
				temperature = int.from_bytes(bytes(data[1:3]), 'little', signed=True) / 10
				self.commands.append(PowerCommand(self.clock(), boiler_id, data[0], temperature))
			elif (function == snc.TemperatureSourceFunction['GET_PROPERTIES']
				and message.getRequestFlag() == snc.RequestFlag.RESPONSE):
				# type, uint16 nominal power, priority, uint16 work time, error.
				if data is None or len(data) not in (7, 8) or any(data[7:]):
					self.error = f'Invalid GET_PROPERTIES for boiler {boiler_id}: {data}'
					return
				self.properties[boiler_id] = (self.clock(), data[6])

	def snapshot(self):
		with self.lock:
			if self.error:
				raise RuntimeError(self.error)
			return list(self.commands), dict(self.properties)

	def output_snapshot(self):
		with self.lock:
			if self.error:
				raise RuntimeError(self.error)
			return list(self.outputs)
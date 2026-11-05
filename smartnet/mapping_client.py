"""Independent mapping readback; never consult the simulator's preset cache."""

import threading

import smartnet.constants as snc


UNDEFINED_MAPPING = 7 << 13
SENSOR_LOCAL = 0
RELAY_LOCAL = 1
PROGRAM_OUTPUT = 5


def pack_mapping(host_id, channel_id, channel_type):
	if (type(host_id) is not int or not 0 <= host_id <= 255
			or type(channel_id) is not int or not 0 <= channel_id < 32
			or type(channel_type) is not int or not 0 <= channel_type < 8):
		raise ValueError('Mapping fields exceed protocol limits')
	return host_id | (channel_id << 8) | (channel_type << 13)


def is_undefined(raw):
	return raw >> 13 == 7


def mappings_equal(left, right):
	return left == right or (is_undefined(left) and is_undefined(right))


class MappingCanError(RuntimeError):
	pass


class _ResponseListener:
	def __init__(self, response_filter, size):
		self.response_filter = response_filter
		self.size = size
		self.event = threading.Event()
		self.response = None

	def on_can_message_received(self, message):
		if (message is not None and message.compare(self.response_filter)
				and len(message.get_data()) == self.size):
			self.response = message
			self.event.set()


class MappingCanClient:
	DEFAULT_TIMEOUT = 2.0

	def __init__(self, timeout=DEFAULT_TIMEOUT):
		if timeout <= 0:
			raise ValueError('CAN timeout must be positive')
		self.timeout = timeout

	def _exchange(self, program_type, host_id, function, prefix, size, payload=None):
		# Lazy import preserves the application's existing mainThread import order.
		from smartnet.message import CanListener, Message
		if type(host_id) is not int or not 1 <= host_id <= 255:
			raise ValueError('An explicit non-broadcast host ID is required')
		response_filter = Message(program_type, host_id, function, snc.RequestFlag.RESPONSE, prefix)
		listener = _ResponseListener(response_filter, size)
		CanListener.subscribe(listener)
		try:
			Message(program_type, host_id, function, snc.RequestFlag.REQUEST,
				prefix if payload is None else payload).send()
			# Cleanup must still work when the scenario/application stop flag is set.
			if not listener.event.wait(self.timeout):
				raise MappingCanError(f'CAN timeout: host={host_id}, function={function}, selector={prefix}')
			return list(listener.response.get_data())
		finally:
			CanListener.unsubscribe(listener)

	@staticmethod
	def _validate_index(index):
		if type(index) is not int or not 0 <= index < 32:
			raise ValueError('Channel index must be in 0..31')

	def _program_mapping(self, program_id, index, parameter_id, raw=None):
		self._validate_index(index)
		prefix = [snc.ProgramType.PROGRAM, parameter_id, index]
		function = snc.RemoteControlFunction.GET_PARAMETER_VALUE
		payload = None
		if raw is not None:
			if type(raw) is not int or not 0 <= raw <= 0xFFFF:
				raise ValueError('Mapping must fit uint16')
			function = snc.RemoteControlFunction.SET_PARAMETER_VALUE
			prefix += [raw & 255, raw >> 8]
			# MODE_UPDATE_NONE: restore this endpoint without propagating changes.
			payload = prefix + [0]
		data = self._exchange(snc.ProgramType.REMOTE_CONTROL, program_id, function,
			prefix, 5 if raw is None else 6, payload)
		if raw is not None and data[5] != 0:
			raise MappingCanError('Controller rejected mapping restoration')
		return data[3] | data[4] << 8

	def read_input(self, program_id, index):
		return self._program_mapping(program_id, index, snc.ProgramParameterId.INPUT_MAPPING)

	def read_output(self, program_id, index):
		return self._program_mapping(program_id, index, snc.ProgramParameterId.OUTPUT_MAPPING)

	def restore_input(self, program_id, index, raw):
		return self._program_mapping(program_id, index, snc.ProgramParameterId.INPUT_MAPPING, raw)

	def restore_output(self, program_id, index, raw):
		return self._program_mapping(program_id, index, snc.ProgramParameterId.OUTPUT_MAPPING, raw)

	def read_relay(self, controller_id, index):
		self._validate_index(index)
		data = self._exchange(snc.ProgramType.CONTROLLER, controller_id,
			snc.ControllerFunction.GET_RELAY_MAPPING, [index], 3)
		return data[1] | data[2] << 8

	def read_channel_counts(self, controller_id):
		return tuple(self._exchange(snc.ProgramType.CONTROLLER, controller_id,
			snc.ControllerFunction.GET_CHANNEL_NUMBER, [], 2))

	def read_controller_type(self, controller_id):
		return self._exchange(snc.ProgramType.CONTROLLER, controller_id,
			snc.ControllerFunction.GET_CONTROLLER_TYPE, [], 1)[0]

	def restore_relay(self, controller_id, index, raw):
		self._validate_index(index)
		if type(raw) is not int or not 0 <= raw <= 0xFFFF:
			raise ValueError('Mapping must fit uint16')
		prefix = [index, raw & 255, raw >> 8]
		self._exchange(snc.ProgramType.CONTROLLER, controller_id,
			snc.ControllerFunction.SET_RELAY_MAPPING, prefix, 3, prefix + [0])
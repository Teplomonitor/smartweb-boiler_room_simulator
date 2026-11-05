import unittest
from unittest.mock import patch

import mainThread  # Import in application order; no services are started.
import smartnet.constants as snc
from smartnet.message import CanListener, Message
from smartnet.mapping_client import (
	MappingCanClient, MappingCanError, UNDEFINED_MAPPING, pack_mapping, mappings_equal,
)


class MappingClientTests(unittest.TestCase):
	def setUp(self):
		self.client = MappingCanClient(timeout=0.001)
		self.before = tuple(CanListener._listeners)

	def tearDown(self):
		self.assertEqual(tuple(CanListener._listeners), self.before)

	def reply(self, request, data, **overrides):
		response = Message(
			overrides.get('program_type', request.get_program_type()),
			overrides.get('host_id', request.getProgramId()),
			overrides.get('function', request.getFunctionId()),
			overrides.get('flag', snc.RequestFlag.RESPONSE), data)
		for listener in tuple(CanListener._listeners):
			if listener not in self.before:
				listener.on_can_message_received(response)

	def test_reads_use_live_get_requests_and_accept_immediate_response(self):
		for method, program_type, function, selector in (
			('read_input', snc.ProgramType.REMOTE_CONTROL,
				snc.RemoteControlFunction.GET_PARAMETER_VALUE, [snc.ProgramType.PROGRAM, 4, 1]),
			('read_output', snc.ProgramType.REMOTE_CONTROL,
				snc.RemoteControlFunction.GET_PARAMETER_VALUE, [snc.ProgramType.PROGRAM, 5, 1]),
			('read_relay', snc.ProgramType.CONTROLLER, snc.ControllerFunction.GET_RELAY_MAPPING, [1]),
		):
			with self.subTest(method=method):
				def send(request):
					self.assertEqual(request.get_program_type(), program_type)
					self.assertEqual(request.getProgramId(), 101)
					self.assertEqual(request.getFunctionId(), function)
					self.assertEqual(request.getRequestFlag(), snc.RequestFlag.REQUEST)
					self.assertEqual(request.get_data(), selector)
					self.reply(request, selector + [7, 0x21])
				with patch.object(Message, 'send', send):
					self.assertEqual(getattr(self.client, method)(101, 1), 0x2107)

	def test_wrong_address_function_flag_index_and_size_are_ignored(self):
		def send(request):
			valid = request.get_data() + [7, 0]
			for overrides in ({'host_id': 102}, {'function': 255}, {'flag': snc.RequestFlag.REQUEST},
					{'program_type': snc.ProgramType.CONTROLLER}):
				self.reply(request, valid, **overrides)
			self.reply(request, [snc.ProgramType.PROGRAM, 4, 2, 7, 0])
			self.reply(request, request.get_data())
			self.reply(request, valid + [99])
		with patch.object(Message, 'send', send), self.assertRaises(MappingCanError):
			self.client.read_input(101, 1)

	def test_channel_counts(self):
		def send(request):
			self.assertEqual(request.get_data(), [])
			self.assertEqual(request.getFunctionId(), snc.ControllerFunction.GET_CHANNEL_NUMBER)
			self.reply(request, [18, 11])
		with patch.object(Message, 'send', send):
			self.assertEqual(self.client.read_channel_counts(7), (18, 11))

	def test_restoration_uses_explicit_no_propagation_flag(self):
		for method in ('restore_input', 'restore_output', 'restore_relay'):
			with self.subTest(method=method):
				def send(request):
					data = request.get_data()
					self.assertEqual(data[-1], 0)  # MODE_UPDATE_NONE
					if method == 'restore_relay':
						self.assertEqual(request.getFunctionId(), snc.ControllerFunction.SET_RELAY_MAPPING)
						self.reply(request, data[:-1])
					else:
						self.assertEqual(request.getFunctionId(), snc.RemoteControlFunction.SET_PARAMETER_VALUE)
						self.reply(request, data[:-1] + [0])
				with patch.object(Message, 'send', send):
					getattr(self.client, method)(101, 0, UNDEFINED_MAPPING)

	def test_rejected_restoration_is_an_error(self):
		def send(request):
			self.reply(request, request.get_data()[:-1] + [1])
		with patch.object(Message, 'send', send), self.assertRaises(MappingCanError):
			self.client.restore_input(101, 0, UNDEFINED_MAPPING)

	def test_send_failure_unsubscribes(self):
		with patch.object(Message, 'send', side_effect=RuntimeError('offline')):
			with self.assertRaises(RuntimeError):
				self.client.read_input(101, 0)

	def test_cleanup_still_exchanges_when_application_is_stopping(self):
		def send(request):
			self.reply(request, request.get_data()[:-1] + [0])
		with patch.object(mainThread, 'taskEnable', return_value=False), patch.object(Message, 'send', send):
			self.client.restore_input(101, 0, UNDEFINED_MAPPING)

	def test_mapping_encoding_and_boundaries(self):
		self.assertEqual(pack_mapping(7, 31, 5), 7 | 31 << 8 | 5 << 13)
		self.assertTrue(mappings_equal(UNDEFINED_MAPPING, 0xFFFF))
		self.assertFalse(mappings_equal(UNDEFINED_MAPPING, 0))
		for fields in ((256, 0, 0), (0, 32, 0), (0, 0, 8), (-1, 0, 0), (True, 0, 0)):
			with self.assertRaises(ValueError):
				pack_mapping(*fields)
		for host, index in ((0, 0), (256, 0), (1, -1), (1, 32)):
			with self.assertRaises(ValueError):
				self.client.read_input(host, index)
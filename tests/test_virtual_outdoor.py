"""Virtual outdoor sources: real wire encoding, fake CAN transport, no application startup."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc
from presets.preset import ProgramPreset, validate_program_presets


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
	spec = importlib.util.spec_from_file_location(name, ROOT / path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


class Sensor:
	def __init__(self):
		self.value = -10
		self.state = 'normal'
	def get_value(self): return self.value
	def set_value(self, value): self.value = value
	def set_mapping(self, value): pass
	def isShort(self): return self.state == 'short'
	def isOpen(self): return self.state == 'open'


class FakeOat:
	def __init__(self, preset):
		self.preset = preset
		self.sensor = Sensor()
	def get_id(self): return self.preset.get_id()
	def getOutdoorTemperature(self): return self.sensor
	def clear(self): pass


def preset(program_type=snc.ProgramType.OUTDOOR_SENSOR, execution='virtual', program_id=103):
	return ProgramPreset(program_type, 'DEFAULT', program_id, 'Test', None, [], [], execution=execution)


class VirtualOutdoorTests(unittest.TestCase):
	def setUp(self):
		with patch.dict(sys.modules, {'mainThread': ModuleType('mainThread')}):
			self.messages = load('outdoor_test_messages', 'smartnet/message.py')
		self.protocol_stub = ModuleType('smartnet.message')
		self.protocol_stub.Message = self.messages.Message
		self.protocol_stub.CanBusInterface = Mock()
		with patch.dict(sys.modules, {'smartnet.message': self.protocol_stub}):
			self.protocol = load('outdoor_protocol_under_test', 'smartnet/outdoor.py')
		oat = ModuleType('programs.oat')
		oat.Oat = FakeOat
		channels = ModuleType('smartnet.channelMapping')
		channels.ChannelMapping = Mock()
		with patch.dict(sys.modules, {'smartnet.message': self.protocol_stub,
			'smartnet.outdoor': self.protocol, 'programs.oat': oat, 'smartnet.channelMapping': channels}):
			self.virtual = load('virtual_outdoor_under_test', 'programs/virtual_outdoor.py')
		self.source = self.virtual.VirtualOutdoor(preset())
		self.bus = self.protocol_stub.CanBusInterface.return_value.get.return_value
		self.clock = patch.object(self.virtual.time, 'monotonic', return_value=0)
		self.now = self.clock.start()
		self.addCleanup(self.clock.stop)

	def test_wire_format_and_parsing(self):
		for value, expected in ((12.5, b'\x7d\x00'), (-15, b'\x6a\xff'), (0, b'\x00\x00')):
			message = self.protocol.make_temperature_message(103, value)
			self.assertEqual(message.get_data(), expected)
			frame = message.smartNetToCanMsg()
			parsed = self.messages.Message()
			parsed.parse(frame)
			self.assertEqual(parsed.get_program_type(), snc.ProgramType.OUTDOOR_SENSOR)
			self.assertEqual(parsed.getProgramId(), 103)
			self.assertEqual(parsed.getFunctionId(), 1)
			self.assertEqual(parsed.getRequestFlag(), snc.RequestFlag.RESPONSE)
			self.assertEqual(bytes(parsed.get_data()), expected)

	def test_invalid_values_and_fault_encoding(self):
		for value in (None, True, float('nan'), float('inf'), -3276.8, 3276.8):
			with self.assertRaises(ValueError):
				self.protocol.make_temperature_message(103, value)
		for program_id in (0, 256, -1, True):
			with self.assertRaises(ValueError):
				self.protocol.make_temperature_message(program_id, 0)
		for state, expected in (('short', b'\x00\x80'), ('open', b'\x01\x80'), ('undefined', b'\x02\x80')):
			self.assertEqual(self.protocol.make_temperature_message(103, None, state).get_data(), expected)

	def test_periodic_publish_and_changed_value(self):
		self.source.publish_temperature()
		self.source.publish_temperature()
		self.assertEqual(self.bus.send.call_count, 1)
		self.now.return_value = 10
		self.source.publish_temperature()
		self.assertEqual(self.bus.send.call_count, 2)
		self.source.sensor.value = 20
		self.source.publish_temperature()
		self.assertEqual(self.bus.send.call_count, 3)

	def test_only_temperature_requests_for_this_source_or_broadcast(self):
		for program_id in (103, 0):
			self.source.on_can_message_received(self.messages.Message(
				snc.ProgramType.OUTDOOR_SENSOR, program_id, 1, snc.RequestFlag.REQUEST))
		self.assertEqual(self.bus.send.call_count, 2)
		for program_type, program_id, function in ((snc.ProgramType.OUTDOOR_SENSOR, 104, 1),
			(snc.ProgramType.REMOTE_CONTROL, 103, 1), (snc.ProgramType.CONTROLLER, 103, 1),
			(snc.ProgramType.OUTDOOR_SENSOR, 103, 2)):
			self.source.on_can_message_received(self.messages.Message(program_type, program_id, function, snc.RequestFlag.REQUEST))
		self.assertEqual(self.bus.send.call_count, 2)

	def test_external_source_stops_publishing(self):
		self.source.on_can_message_received(self.protocol.make_temperature_message(104, 0))
		with self.assertRaisesRegex(RuntimeError, 'Competing'):
			self.source.publish_temperature()
		self.bus.send.assert_not_called()

	def test_own_loopback_is_not_a_conflict(self):
		self.source.on_can_message_received(self.protocol.make_temperature_message(103, 0))
		self.source.publish_temperature()
		self.bus.send.assert_called_once()

	def test_close_prevents_publications_and_request_replies(self):
		self.source.clear()
		self.source.publish_temperature(force=True)
		self.source.on_can_message_received(self.messages.Message(snc.ProgramType.OUTDOOR_SENSOR, 103, 1, snc.RequestFlag.REQUEST))
		self.bus.send.assert_not_called()

	def test_send_failure_is_not_swallowed(self):
		self.bus.send.side_effect = RuntimeError('transport failure')
		with self.assertRaisesRegex(RuntimeError, 'transport failure'):
			self.source.publish_temperature()
		self.assertIsNone(self.source._last_payload)
		self.source.on_can_message_received(self.messages.Message(snc.ProgramType.OUTDOOR_SENSOR, 103, 1, snc.RequestFlag.REQUEST))
		with self.assertRaisesRegex(RuntimeError, 'publication failed'):
			self.source.publish_temperature()


class PresetExecutionTests(unittest.TestCase):
	def test_default_remains_real(self):
		self.assertFalse(ProgramPreset(2, 'DEFAULT', 103, 'Street', None, [], []).is_virtual())
		with self.assertRaises(ValueError):
			preset(execution='typo')

	def test_validate_rejects_conflicts_duplicates_and_unsupported_types(self):
		validate_program_presets([preset()])
		for programs in ([preset(), preset(execution='real', program_id=104)],
			[preset(), preset(program_id=104)], [preset(), preset()],
			[preset(program_type=snc.ProgramType.BOILER)]):
			with self.assertRaises(ValueError):
				validate_program_presets(programs)

	def test_virtual_load_never_adds_or_binds_on_controller(self):
		controller = Mock()
		self.assertTrue(preset().loadPreset(controller))
		controller.addProgramFromPreset.assert_called_once()
		controller.sendProgramAddRequest.assert_not_called()
		controller.addProgramFromPreset.return_value.bind_input.assert_not_called()

	def test_controller_matches_only_real_programs(self):
		dependencies = {}
		for name in ('programs.factory', 'smartnet.remoteControl', 'smartnet.message', 'smartnet.message_log', 'consoleLog'):
			dependencies[name] = ModuleType(name)
		dependencies['smartnet.message_log'].MessageLogReader = Mock()
		dependencies['consoleLog'].print_log = Mock()
		dependencies['consoleLog'].print_error = Mock()
		with patch.dict(sys.modules, dependencies):
			controller_class = load('controller_execution_under_test', 'controllers/controller.py').Controller
		controller = controller_class(123)
		controller.readControllerProgramList = Mock(return_value=[{'id': 101, 'type': snc.ProgramType.SNOWMELT}])
		controller.addProgramFromPreset = Mock()
		controller.initController(False, [preset(snc.ProgramType.SNOWMELT, 'real', 101), preset()])
		self.assertEqual(controller.addProgramFromPreset.call_count, 2)
		controller.readControllerProgramList.return_value.append({'id': 104, 'type': snc.ProgramType.OUTDOOR_SENSOR})
		with self.assertRaisesRegex(ValueError, 'Remove the real outdoor'):
			controller.initController(False, [preset()])


if __name__ == '__main__':
	unittest.main()
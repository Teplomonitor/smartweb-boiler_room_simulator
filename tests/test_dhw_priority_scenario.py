"""CAN priority-frame filtering and DHW request-condition unit tests."""

import threading
import importlib.util
from pathlib import Path
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import smartnet.constants as snc


def load_priority_scenario_base():
	root = Path(__file__).resolve().parents[1]
	dhw_base = ModuleType('scenario.base.dhw')
	dhw_base.DhwScenario = type('DhwScenario', (), {})
	message = ModuleType('smartnet.message')
	message.CanListener = SimpleNamespace(subscribe=Mock(), unsubscribe=Mock())
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	console = ModuleType('consoleLog')
	console.print_error = Mock()
	console.print_log = Mock()
	module_name = 'dhw_priority_base_under_test'
	spec = importlib.util.spec_from_file_location(
		module_name, root / 'scenario/base/dhw_priority.py',
	)
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {
		'scenario.base.dhw': dhw_base,
		'smartnet.message': message,
		'smartnet.remoteControl': remote,
		'consoleLog': console,
	}):
		spec.loader.exec_module(module)
	return module.DhwPriorityScenario


DhwPriorityScenario = load_priority_scenario_base()


class TestDhwPriorityScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = object.__new__(DhwPriorityScenario)
		self.scenario._priority_lock = threading.Lock()
		self.scenario._priority_events = []
		self.scenario._dhw = Mock()
		self.scenario._dhw.get_id.return_value = 101

	@staticmethod
	def make_message(program_type=snc.ProgramType.CONSUMER, program_id=0,
			function=snc.ConsumerFunction['GIVE_WAY'], request=snc.RequestFlag.REQUEST,
			data=(101, 5, 102)):
		return SimpleNamespace(
			get_program_type=lambda: program_type,
			getProgramId=lambda: program_id,
			getFunctionId=lambda: function,
			getRequestFlag=lambda: request,
			get_data=lambda: data,
		)

	def test_captures_only_dhw_priority_broadcast_requests(self):
		self.scenario.on_can_message_received(self.make_message())
		self.assertEqual(len(self.scenario._priority_events), 1)
		self.assertEqual(self.scenario._priority_events[0][1:], (
			snc.ConsumerFunction['GIVE_WAY'], (101, 5, 102),
		))

	def test_ignores_non_dhw_or_non_request_frames(self):
		messages = (
			self.make_message(program_type=snc.ProgramType.DHW),
			self.make_message(program_id=7),
			self.make_message(function=snc.ConsumerFunction['SET_COOLING']),
			self.make_message(request=snc.RequestFlag.RESPONSE),
			self.make_message(data=(102, 5, 102)),
			self.make_message(data=(101,)),
		)
		for message in messages:
			self.scenario.on_can_message_received(message)
		self.assertEqual(self.scenario._priority_events, [])

	def test_standard_scheme_requires_active_request_and_hot_generator(self):
		self.scenario._read_consumer_temperature = Mock(side_effect=(55, 70))
		self.assertTrue(self.scenario._required_and_generator_temperatures_match(False))
		self.scenario._read_consumer_temperature = Mock(side_effect=(0, 70))
		self.assertFalse(self.scenario._required_and_generator_temperatures_match(False))
		self.scenario._read_consumer_temperature = Mock(side_effect=(55, 55))
		self.assertFalse(self.scenario._required_and_generator_temperatures_match(False))

	def test_flow_through_requires_request_above_generator_temperature(self):
		self.scenario._read_consumer_temperature = Mock(side_effect=(55, 35))
		self.assertTrue(self.scenario._required_and_generator_temperatures_match(True))
		self.scenario._read_consumer_temperature = Mock(side_effect=(55, 55))
		self.assertFalse(self.scenario._required_and_generator_temperatures_match(True))
		self.scenario._read_consumer_temperature = Mock(side_effect=(None, 35))
		self.assertFalse(self.scenario._required_and_generator_temperatures_match(True))

	def test_priority_inputs_use_generator_sensor_not_numeric_temperature(self):
		dhw_sensor = self.scenario._dhw.get_temperature.return_value
		generator_sensor = Mock()
		self.scenario._generator = Mock()
		self.scenario._generator.get_temperature.return_value = 70.0
		self.scenario._generator.get_input_channel.return_value = generator_sensor
		self.scenario.set_sensor_value = Mock()

		self.assertEqual(self.scenario._get_test_sensors(False), [dhw_sensor, generator_sensor])
		self.scenario._set_priority_test_inputs(False)
		self.scenario.set_sensor_value.assert_any_call(dhw_sensor, self.scenario.DHW_COLD_TEMPERATURE)
		self.scenario.set_sensor_value.assert_any_call(generator_sensor, self.scenario.GENERATOR_TEMPERATURE)
		self.scenario._generator.get_temperature.assert_not_called()

	def test_flow_through_uses_generator_sensor_and_flow_channel(self):
		self.scenario._generator = Mock()
		generator_sensor = self.scenario._generator.get_input_channel.return_value
		flow_sensor = self.scenario._dhw.get_input_channel.return_value
		self.scenario.set_sensor_value = Mock()

		self.assertEqual(self.scenario._get_test_sensors(True),
			[self.scenario._dhw.get_temperature.return_value, generator_sensor, flow_sensor])
		self.scenario._set_priority_test_inputs(True)
		self.scenario.set_sensor_value.assert_any_call(generator_sensor,
			self.scenario.FLOW_THROUGH_GENERATOR_TEMPERATURE)
		self.scenario.set_sensor_value.assert_any_call(flow_sensor, self.scenario.FLOW_RATE)


if __name__ == '__main__':
	unittest.main()

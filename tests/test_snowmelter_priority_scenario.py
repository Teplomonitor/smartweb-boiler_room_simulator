"""Checklist 5.1.2.1: strict threshold, CAN filtering and failure cleanup."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc
from tests.test_scenario_steps import Sensor, load_steps


class Input(Sensor):
	def __init__(self, index, value, **kwargs):
		super().__init__(value, **kwargs)
		self.index = index
		self.mapped = True

	def get_id(self): return self.index
	def is_mapped(self): return self.mapped


def load_module(name, relative_path):
	path = Path(__file__).resolve().parents[1] / relative_path
	spec = importlib.util.spec_from_file_location(name, path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


class SnowmelterPriorityScenarioTests(unittest.TestCase):
	def setUp(self):
		self.time = 0
		self.cancel_at = None
		self.inclusive_threshold = False
		self.send_requests = True
		self.source_id = 101
		self.missing_input = False
		self.steps = load_steps()
		parent = ModuleType('scenario.base.snowmelter')
		class Parent:
			def __init__(self, *args): pass
		parent.SnowmelterScenario = Parent
		console = ModuleType('consoleLog')
		console.print_log = Mock()
		console.print_error = Mock()
		message = ModuleType('smartnet.message')
		message.CanListener = SimpleNamespace(subscribe=Mock(), unsubscribe=Mock())
		remote = ModuleType('smartnet.remoteControl')
		remote.RemoteControlParameter = Mock(side_effect=self.remote_parameter)
		with patch.dict(sys.modules, {
			'scenario.base.snowmelter': parent, 'scenario.steps': self.steps,
			'consoleLog': console, 'smartnet.message': message, 'smartnet.remoteControl': remote,
		}):
			capture = load_module('capture_under_test', 'scenario/base/consumer_priority.py')
			with patch.dict(sys.modules, {'scenario.base.consumer_priority': capture}):
				base = load_module('snowmelter_priority_under_test', 'scenario/base/snowmelter_priority.py')
				with patch.dict(sys.modules, {'scenario.base.snowmelter_priority': base}):
					module = load_module('snowmelter_priority_list_under_test',
						'scenario/list/snowmelter/scenario_snowmelter_priority_5_1_2_1.py')
		self.listener = message.CanListener
		self.scenario = module.Scenario(None, None)
		self.scenario._manualSensorsList = []
		self.scenario.wait = self.wait
		self.scenario.wait_event = self.wait_event
		self.scenario.set_sensor_value = self.set_sensor
		self.scenario.setOutdoorTemperature = lambda value: self.set_sensor(self.outdoor, value)
		self.direct, self.backward, self.plate = Input(0, 20), Input(1, 25), Input(2, 5)
		self.outdoor = Input(4, -10, manual=True, state='short')
		self.scenario._outdoor = SimpleNamespace(getOutdoorTemperature=lambda: self.outdoor)
		self.scenario._snowmelter = SimpleNamespace(
			get_id=lambda: 101, getDirectFlowTemperature=lambda: self.direct,
			getBackwardFlowTemperature=lambda: self.backward, getPlateTemperature=lambda: self.plate,
			read_parameter_value=Mock(return_value=0), write_parameter=Mock(return_value=True),
		)
		for method, value in (
			('readMinOutdoorTemperature', -15), ('readMaxOutdoorTemperature', 3),
			('readRequiredFlowTemperature', 40), ('readRequiredPlateTemperatureValue', 5),
			('readFrostProtectionTemperatureValue', 10),
		):
			setattr(self.scenario, method, Mock(return_value=value))
		self.clock = patch.object(self.steps.time, 'monotonic', side_effect=lambda: self.time)
		self.clock.start()
		self.addCleanup(self.clock.stop)

	def remote_parameter(self, programType, parameterId, programId, parameterIndex=None):
		def value():
			if programType == snc.ProgramType.CONSUMER:
				return 40
			if programType == snc.ProgramType.SNOWMELT:
				return self.outdoor.value
			if self.missing_input:
				return None
			return [self.direct, self.backward, self.plate][parameterIndex].value
		return SimpleNamespace(read=lambda: True, get_value=value)

	def set_sensor(self, sensor, value):
		sensor.set_manual(True)
		sensor.set_value(value, True)
		if sensor not in self.scenario._manualSensorsList:
			self.scenario._manualSensorsList.append(sensor)

	def wait(self, duration):
		self.time += duration
		if self.cancel_at is not None and self.time >= self.cancel_at:
			raise InterruptedError('cancelled')
		deficit = 40 - self.direct.value
		request = deficit >= 5 if self.inclusive_threshold else deficit > 5
		if self.send_requests and request and self.time % 10 == 0:
			self.scenario.on_can_message_received(self.make_message(data=(self.source_id, 5, 102)))
		return True

	def wait_event(self, condition, timeout):
		deadline = self.time + timeout
		while self.time < deadline:
			self.wait(1)
			if condition():
				return True
		return False

	@staticmethod
	def make_message(program_type=snc.ProgramType.CONSUMER, program_id=0,
			function=snc.ConsumerFunction['GIVE_WAY'], request=snc.RequestFlag.REQUEST,
			data=(101, 5, 102)):
		return SimpleNamespace(get_program_type=lambda: program_type, getProgramId=lambda: program_id,
			getFunctionId=lambda: function, getRequestFlag=lambda: request, get_data=lambda: data)

	def assert_restored(self):
		self.assertEqual([self.direct.value, self.backward.value, self.plate.value, self.outdoor.value],
			[20, 25, 5, -10])
		self.assertEqual([self.direct.manual, self.backward.manual, self.plate.manual, self.outdoor.manual],
			[False, False, False, True])
		self.assertTrue(self.outdoor.isShort())
		self.assertEqual(self.scenario._manualSensorsList, [])
		self.assertFalse(self.scenario._priority_listener_active)
		self.scenario._snowmelter.write_parameter.assert_called_with('workMode', 0)

	def test_strict_boundary_and_request_succeed(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertGreaterEqual(self.time, self.scenario.NO_REQUEST_DURATION)
		self.listener.subscribe.assert_called_once_with(self.scenario)
		self.listener.unsubscribe.assert_called_once_with(self.scenario)
		self.assert_restored()

	def test_inclusive_threshold_fails(self):
		self.inclusive_threshold = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_missing_request_fails(self):
		self.send_requests = False
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_foreign_request_cannot_pass(self):
		self.source_id = 102
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_unconfirmed_delivery_fails(self):
		self.missing_input = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.listener.subscribe.assert_not_called()
		self.assert_restored()

	def test_cancellation_restores_and_unsubscribes(self):
		self.cancel_at = 10
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.listener.unsubscribe.assert_called_once_with(self.scenario)
		self.assert_restored()

	def test_missing_parameter_or_mapping_fails_before_manual_inputs(self):
		for failure in ('parameter', 'mapping'):
			with self.subTest(failure=failure):
				self.scenario.readRequiredFlowTemperature.return_value = None if failure == 'parameter' else 40
				self.direct.mapped = failure != 'mapping'
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.listener.subscribe.assert_not_called()
				self.assert_restored()

	def test_failed_mode_activation_restores_inputs(self):
		self.scenario._snowmelter.write_parameter.side_effect = (False, True)
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_failed_mode_restore_marks_failure(self):
		self.scenario._snowmelter.write_parameter.side_effect = (True, False)
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_frame_filter_and_event_reset(self):
		for message in (
			self.make_message(program_type=snc.ProgramType.SNOWMELT),
			self.make_message(program_id=101),
			self.make_message(function=snc.ConsumerFunction['SET_COOLING']),
			self.make_message(request=snc.RequestFlag.RESPONSE),
			self.make_message(data=(102, 5, 102)), self.make_message(data=None),
			self.make_message(data=(101,)),
		):
			self.scenario.on_can_message_received(message)
		self.assertEqual(self.scenario._priority_events, [])
		self.scenario.on_can_message_received(self.make_message())
		self.assertTrue(self.scenario._has_priority_event(snc.ConsumerFunction['GIVE_WAY']))
		self.scenario._clear_priority_events()
		self.assertFalse(self.scenario._has_priority_event(snc.ConsumerFunction['GIVE_WAY']))


if __name__ == '__main__':
	unittest.main()
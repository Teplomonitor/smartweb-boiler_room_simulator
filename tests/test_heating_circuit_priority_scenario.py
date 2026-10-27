"""Scripted controller replies and CAN broadcasts, not firmware integration."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc
from tests.test_scenario_steps import Sensor, load_steps


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
	spec = importlib.util.spec_from_file_location(name, ROOT / path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


class Input(Sensor):
	def __init__(self, index, value, mapped=True, **kwargs):
		super().__init__(value, **kwargs)
		self.index, self.mapped = index, mapped

	def get_id(self): return self.index
	def is_mapped(self): return self.mapped


class HeatingCircuitPriorityTests(unittest.TestCase):
	def test_preset_has_correct_order_and_sensor_mappings(self):
		remote = ModuleType('smartnet.remoteControl')
		remote.RemoteControlParameter = Mock()
		with patch.dict(sys.modules, {'smartnet.remoteControl': remote}):
			preset = load_module('heating_priority_preset_test', 'presets/list/heating_circuit_priority.py')
		programs, controllers = preset.get_presets_list()
		self.assertEqual([program.get_id() for program in programs], [101, 102, 103, 104])
		self.assertEqual([program.get_scheme() for program in programs[:3]],
			['CIRCUIT_MIXED', 'CIRCUIT_DIRECT', 'CIRCUIT_MIXED'])
		self.assertEqual([bool(program.get_inputs() and program.getInput(0)) for program in programs[:3]],
			[True, False, False])
		self.assertEqual(len(controllers), 1)

	def setUp(self):
		self.time = 0
		self.inclusive = False
		self.send_requests = True
		self.false_request = None
		self.cancel_at = None
		self.values = {}
		self.initial = {}
		self.fail_restore = False
		self.flow = Input(0, 25, manual=True)
		self.source = Input(0, 60)
		self.programs = {}
		for name, program_id, scheme, mapped in (
			('mixed', 101, 'CIRCUIT_MIXED', True),
			('direct', 102, 'CIRCUIT_DIRECT', False),
			('mixed_without_sensor', 103, 'CIRCUIT_MIXED', False),
		):
			inputs = {'temperature': self.flow if mapped else Input(0, None, False)}
			inputs.update({key: Input(index, None, False) for index, key in enumerate(
				('thermostat', 'outsideRequest', 'pumpControl'), 1)})
			outputs = {'pump': Input(3, None), 'analogValve': Input(0, None, name != 'direct')}
			self.programs[name] = self.make_program(program_id, inputs, outputs)
			self.values[(program_id, snc.ProgramType.PROGRAM, snc.ProgramParameterId.SCHEME, None)] = snc.ProgramScheme[scheme]
			self.values[(program_id, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID, None)] = 104
		boiler = self.make_program(104, {'temperature': self.source}, {})
		self.programs['boiler'] = boiler
		steps = load_steps()
		parent = ModuleType('scenario.scenario')
		parent.Scenario = type('Parent', (), {'__init__': lambda self, *args: None})
		console = ModuleType('consoleLog')
		console.print_log = Mock()
		console.print_error = Mock()
		message = ModuleType('smartnet.message')
		message.CanListener = SimpleNamespace(subscribe=Mock(), unsubscribe=Mock())
		remote = ModuleType('smartnet.remoteControl')
		remote.RemoteControlParameter = Mock(side_effect=self.parameter)
		with patch.dict(sys.modules, {
			'scenario.scenario': parent, 'scenario.steps': steps, 'consoleLog': console,
			'smartnet.message': message, 'smartnet.remoteControl': remote,
		}):
			capture = load_module('capture_priority_test', 'scenario/base/consumer_priority.py')
			with patch.dict(sys.modules, {'scenario.base.consumer_priority': capture}):
				base = load_module('heating_priority_test', 'scenario/base/heating_circuit_priority.py')
				with patch.dict(sys.modules, {'scenario.base.heating_circuit_priority': base}):
					self.modules = [load_module(f'heating_priority_list_{index}',
						f'scenario/list/heating_circuit/scenario_heating_circuit_priority_5_1_3_{index}.py')
						for index in (1, 2)]
		self.scenario = self.modules[0].Scenario(None, None)
		self.scenario._programList = self.programs
		self.scenario._manualSensorsList = []
		self.scenario.wait = self.wait
		self.scenario.set_sensor_value = self.set_sensor
		for program, program_type, parameter_id, _ in self.scenario._settings():
			self.values[(program.get_id(), program_type, parameter_id, None)] = 1
		self.initial = self.values.copy()
		self.clock = patch.object(steps.time, 'monotonic', side_effect=lambda: self.time)
		self.clock.start()
		self.addCleanup(self.clock.stop)
		self.listener = message.CanListener
		self.console = console

	@staticmethod
	def make_program(program_id, inputs, outputs):
		return SimpleNamespace(get_id=lambda: program_id, get_input_channel=lambda key: inputs[key],
			get_output_channel=lambda key: outputs[key])

	def parameter(self, programType, parameterId, programId, parameterIndex=None, parameterValue=None):
		key = (programId, programType, parameterId, parameterIndex)
		def read_value():
			if programType == snc.ProgramType.PROGRAM and parameterId == snc.ProgramParameterId.INPUT:
				return self.flow.value if programId == 101 else self.source.value
			if programType == snc.ProgramType.CONSUMER and parameterId == snc.ConsumerParameterId.REQUIRED_TEMPERATURE:
				return self.values[(programId, snc.ProgramType.CIRCUIT,
					snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, None)]
			return self.values.get(key)
		def write():
			if self.fail_restore and parameterValue == 1:
				return False
			self.values[key] = parameterValue
			return True
		return SimpleNamespace(read=lambda: read_value() is not None, get_value=read_value, write=write)

	def set_sensor(self, sensor, value):
		sensor.set_manual(True)
		sensor.set_value(value, True)
		if sensor not in self.scenario._manualSensorsList:
			self.scenario._manualSensorsList.append(sensor)

	def wait(self, duration):
		self.time += duration
		if self.cancel_at is not None and self.time >= self.cancel_at:
			raise InterruptedError('cancelled')
		if self.scenario._priority_listener_active and self.time % 10 == 0:
			program = self.scenario._circuit
			program_id = program.get_id()
			band = self.values[(program_id, snc.ProgramType.HEATING_CIRCUIT,
				snc.HeatingCircuitParameterId.VALVE_OPEN_PROPORTIONAL_BAND, None)]
			request = program_id == 101 and (
				self.flow.value <= 40 - band if self.inclusive else self.flow.value < 40 - band)
			if self.false_request == program_id:
				request = True
			if request and self.send_requests:
				frame = SimpleNamespace(get_program_type=lambda: snc.ProgramType.CONSUMER,
					getProgramId=lambda: 0, getRequestFlag=lambda: snc.RequestFlag.REQUEST,
					getFunctionId=lambda: snc.ConsumerFunction['GIVE_WAY'],
					get_data=lambda: (program_id, 5, 104))
				self.scenario.on_can_message_received(frame)
		return True

	def assert_restored(self):
		self.assertEqual(self.flow.value, 25)
		self.assertTrue(self.flow.manual)
		self.assertEqual(self.source.value, 60)
		self.assertFalse(self.source.manual)
		self.assertEqual(self.scenario._manualSensorsList, [])
		self.assertFalse(self.scenario._priority_listener_active)
		self.assertEqual(self.values, self.initial)

	def test_both_scenarios_pass_and_restore(self):
		for module in self.modules:
			with self.subTest(id=module.Scenario(None, None).get_checklist_id()):
				self.scenario.__class__ = module.Scenario
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'OK')
				self.assert_restored()

	def test_inclusive_threshold_fails(self):
		self.inclusive = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_no_broadcast_fails_positive_control(self):
		self.scenario.__class__ = self.modules[1].Scenario
		self.send_requests = False
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_spurious_request_from_unmapped_circuit_fails(self):
		for program_id in (102, 103):
			with self.subTest(program_id=program_id):
				self.scenario.__class__ = self.modules[1].Scenario
				self.false_request = program_id
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_restored()

	def test_cancellation_restores_and_unsubscribes(self):
		self.cancel_at = 10
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.listener.unsubscribe.assert_called()
		self.assert_restored()

	def test_restore_failure_marks_failure_and_attempts_other_settings(self):
		self.fail_restore = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertFalse(self.scenario._priority_listener_active)
		self.assertEqual(self.flow.value, 25)
		self.assertEqual(self.source.value, 60)
		self.assertTrue(self.console.print_error.called)

	def test_bad_topology_fails_before_changes(self):
		self.programs['direct'].get_input_channel('temperature').mapped = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.values, self.initial)
		self.listener.subscribe.assert_not_called()


if __name__ == '__main__':
	unittest.main()
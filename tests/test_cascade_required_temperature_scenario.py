"""Scenario 3.6.4 control-flow tests, not firmware integration tests."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
	spec = importlib.util.spec_from_file_location(name, ROOT / path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


parent = ModuleType('scenario.scenario')
parent.Scenario = object
main_thread = ModuleType('mainThread')
main_thread.taskEnable = lambda: True
with patch.dict(sys.modules, {'scenario.scenario': parent, 'mainThread': main_thread}):
	from smartnet.channelMapping import InputChannel, ChannelMapping
	from presets.list import cascade_manager_3_6_4 as preset
	base = load_module('cascade_temperature_base_test', 'scenario/base/cascade_manager.py')
	with patch.dict(sys.modules, {'scenario.base.cascade_manager': base}):
		Scenario = load_module('cascade_temperature_test', 'scenario/list/cascade_manager/scenario_cascade_manager_3_6_4.py').Scenario


class TestCascadeRequiredTemperature(unittest.TestCase):
	def setUp(self):
		self.scenario = Scenario()
		self.scenario._manualSensorsList = []
		self.scenario._programList = {}
		self.sensors = []
		for index, name in enumerate(self.scenario.get_required_programs()):
			program = Mock()
			program.get_id.return_value = index + 101
			self.scenario._programList[name] = program
			if index < 3:
				sensor = InputChannel(mapping=ChannelMapping(index, 'CHANNEL_SENSOR', 123))
				sensor.set_value(25)
				program.get_input_channel.return_value = sensor
				self.sensors.append(sensor)
		self.values = {}
		self.originals = {}
		self.failed_write = None
		self.bad_requests = False
		self.selection = max
		self.observed = []
		self.scenario.read_parameter = self.read_parameter
		self.scenario.write_parameter = self.write_parameter
		self.scenario.set_sensor_value = self.set_sensor_value
		self.scenario.wait_state_permanence = self.wait_stable

	def key(self, program, program_type, parameter_id):
		return program.get_id(), program_type, parameter_id

	def read_parameter(self, program, program_type, parameter_id):
		key = self.key(program, program_type, parameter_id)
		if program_type == snc.ProgramType.TEMPERATURE_SOURCE:
			return self.selection(self.requests())
		if program_type == snc.ProgramType.CONSUMER and parameter_id == snc.ConsumerParameterId.REQUIRED_TEMPERATURE:
			if self.bad_requests:
				return 0
			return self.values[(program.get_id(), snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE)]
		if key not in self.values:
			self.values[key] = self.originals[key] = 20
		return self.values[key]

	def write_parameter(self, program, program_type, parameter_id, value):
		key = self.key(program, program_type, parameter_id)
		self.values[key] = value
		if (key, value) == self.failed_write:
			raise RuntimeError('Test write failure after delivery')

	def requests(self):
		return tuple(
			self.values[(program_id, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE)]
			for program_id in (101, 102)
		)

	def set_sensor_value(self, sensor, value):
		sensor.set_manual(True)
		sensor.set_value(value, True)
		self.scenario._manualSensorsList.append(sensor)

	def wait_stable(self, predicate, duration, timeout):
		self.observed.append((self.requests(), self.selection(self.requests())))
		return predicate() and predicate()

	def assert_restored(self, status):
		self.assertEqual(self.scenario._status, status)
		self.assertEqual(self.values, self.originals)
		self.assertEqual([sensor.get_value() for sensor in self.sensors], [25] * 3)
		self.assertFalse(any(sensor.isManual() for sensor in self.sensors))
		self.assertEqual(self.scenario._manualSensorsList, [])

	def test_success_checks_leader_change_and_decrease(self):
		self.scenario.run()
		self.assert_restored('OK')
		self.assertEqual(self.observed, [((40, 50), 50), ((60, 50), 60), ((40, 50), 50)])
		self.assertEqual(self.scenario.get_checklist_id(), '3.6.4')
		self.assertTrue(self.scenario.force_preset_load())
		self.assertEqual(self.scenario.get_default_preset(), 'cascade_manager_3_6_4')

	def test_wrong_maximum_is_rejected(self):
		self.selection = min
		self.scenario.run()
		self.assert_restored('FAIL')

	def test_stale_cascade_temperature_is_rejected(self):
		self.selection = lambda requests: 50
		self.scenario.run()
		self.assert_restored('FAIL')

	def test_wrong_consumer_request_is_rejected(self):
		self.bad_requests = True
		self.scenario.run()
		self.assert_restored('FAIL')

	def test_failed_write_is_restored(self):
		self.failed_write = ((101, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE), 60)
		self.scenario.run()
		self.assert_restored('FAIL')

	def test_read_failure_prevents_changes(self):
		self.scenario.read_parameter = Mock(side_effect=RuntimeError('Read failure'))
		self.scenario.run()
		self.assert_restored('FAIL')

	def test_external_stop_restores_state(self):
		self.scenario.wait_state_permanence = Mock(side_effect=InterruptedError())
		with self.assertRaises(InterruptedError):
			self.scenario.run()
		self.assert_restored('FAIL')

	def test_manual_sensor_state_is_preserved(self):
		self.sensors[0].set_manual(True)
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertTrue(self.sensors[0].isManual())
		self.assertEqual(self.sensors[0].get_value(), 25)

	def test_restore_failure_marks_scenario_failed(self):
		self.failed_write = ((101, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE), 20)
		self.scenario.run()
		self.assert_restored('FAIL')

	def test_preset_topology_and_mappings(self):
		programs, controllers = preset.get_presets_list()
		self.assertEqual(len(controllers), 1)
		self.assertEqual(len({program.get_id() for program in programs}), 5)
		first, second, cascade, *boilers = programs
		for circuit in (first, second):
			self.assertEqual(circuit.get_type(), snc.ProgramType.HEATING_CIRCUIT)
			self.assertEqual(circuit.getSettings().getSource(), cascade.get_id())
		self.assertEqual(cascade.get_type(), snc.ProgramType.CASCADE_MANAGER)
		self.assertFalse(cascade.get_inputs()[1].is_mapped())
		self.assertEqual(cascade.getSettings().getSourceList()[:2], [boiler.get_id() for boiler in boilers])
		for boiler in boilers:
			self.assertEqual(boiler.get_type(), snc.ProgramType.BOILER)
			self.assertFalse(any(mapping.is_mapped() for mapping in boiler.get_inputs()))
		for get_channels in (lambda program: program.get_inputs(), lambda program: program.get_outputs()):
			mappings = [mapping.get_raw() for program in programs for mapping in get_channels(program) if mapping.is_mapped()]
			self.assertEqual(len(mappings), len(set(mappings)))


if __name__ == '__main__':
	unittest.main()
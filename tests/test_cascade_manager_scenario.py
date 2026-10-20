"""Cascade 3.6.3 contract/control-flow tests; not controller integration tests."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
	spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


parent = ModuleType('scenario.scenario')
parent.Scenario = object
main_thread = ModuleType('mainThread')
main_thread.taskEnable = lambda: True
with patch.dict(sys.modules, {'scenario.scenario': parent, 'mainThread': main_thread}):
	import smartnet.remoteControl as remote
	from smartnet.channelMapping import InputChannel, ChannelMapping
	from presets.list import cascade_manager_3_6_3 as preset
	base = load_module('cascade_base_test', 'scenario/base/cascade_manager.py')
	with patch.dict(sys.modules, {'scenario.base.cascade_manager': base}):
		Scenario = load_module('cascade_scenario_test', 'scenario/list/cascade_manager/scenario_cascade_manager_3_6_3.py').Scenario


class TestCascadeProtocolAndPreset(unittest.TestCase):
	def test_proportional_band_has_temperature_encoding(self):
		parameter = remote.RemoteControlParameter(
			programType=snc.ProgramType.CASCADE_MANAGER,
			parameterId=snc.CascadeManagerParameterId.PARAM_P_FACTOR,
			programId=102,
		)
		self.assertEqual(parameter.getParameterType(), 'TEMPERATURE')
		self.assertEqual(parameter.getParameterSize(), 2)
		for value, data in ((20, [200, 0]), (25.6, [0, 1]), (100, [232, 3])):
			with self.subTest(value=value):
				self.assertEqual(parameter.valueToData(value), data)
				self.assertEqual(parameter.dataToValue(data), value)

	def test_proportional_band_write_and_read_messages(self):
		parameter = remote.RemoteControlParameter(
			programType=snc.ProgramType.CASCADE_MANAGER,
			parameterId=snc.CascadeManagerParameterId.PARAM_P_FACTOR,
			programId=102, parameterValue=20,
		)
		response = Mock()
		response.get_data.return_value = [4, 7, 0]
		with patch.object(remote.sm.Message, 'send', autospec=True, return_value=response) as send:
			self.assertTrue(parameter.write())
			request = send.call_args.args[0]
			self.assertEqual(request.get_data(), [4, 7, 200, 0])
			self.assertEqual(request.getProgramId(), 102)
			self.assertEqual(request.get_program_type(), snc.ProgramType.REMOTE_CONTROL)
			response.get_data.return_value = [4, 7, 0, 1]
			self.assertTrue(parameter.read())
			self.assertEqual(send.call_args.args[0].get_data(), [4, 7])
			self.assertEqual(parameter.get_value(), 25.6)

	def test_preset_topology_and_modulating_outputs(self):
		programs, controllers = preset.get_presets_list()
		self.assertEqual(len(controllers), 1)
		self.assertEqual(len({program.get_id() for program in programs}), 4)
		dhw, cascade, *boilers = programs
		self.assertEqual(dhw.getSettings().getSource(), cascade.get_id())
		self.assertEqual(cascade.get_type(), snc.ProgramType.CASCADE_MANAGER)
		self.assertTrue(cascade.get_inputs()[0].is_mapped())
		self.assertEqual(cascade.getSettings().getSourceList()[:2], [boiler.get_id() for boiler in boilers])
		outputs = []
		for boiler in boilers:
			self.assertEqual(boiler.get_type(), snc.ProgramType.BOILER)
			self.assertFalse(any(mapping.is_mapped() for mapping in boiler.get_inputs()))
			self.assertEqual([mapping.is_mapped() for mapping in boiler.get_outputs()], [True, False, False, True])
		for program in programs:
			outputs.extend(mapping.get_raw() for mapping in program.get_outputs() if mapping.is_mapped())
		self.assertEqual(len(outputs), len(set(outputs)))


class TestCascadeScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = Scenario()
		self.scenario._manualSensorsList = []
		self.programs = {name: Mock() for name in ('cascade', 'boiler_1', 'boiler_2', 'dhw')}
		for name, program_id in (('cascade', 102), ('boiler_1', 103), ('boiler_2', 104), ('dhw', 101)):
			self.programs[name].get_id.return_value = program_id
		self.scenario._programList = self.programs
		self.sensors = []
		for index in range(2):
			sensor = InputChannel(mapping=ChannelMapping(index, 'CHANNEL_SENSOR', 123))
			sensor.set_value(30)
			self.sensors.append(sensor)
		self.collector, self.dhw_sensor = self.sensors
		self.programs['cascade'].get_input_channel.return_value = self.collector
		self.programs['dhw'].get_temperature.return_value = self.dhw_sensor
		for name in ('boiler_1', 'boiler_2'):
			self.programs[name].get_input_channel.return_value.is_mapped.return_value = False
		cascade_id = snc.CascadeManagerParameterId
		self.values = {
			(102, snc.ProgramType.CASCADE_MANAGER, key): value for key, value in (
				(cascade_id.PARAM_P_FACTOR, 25), (cascade_id.PARAM_I_FACTOR, 3),
				(cascade_id.PARAM_D_FACTOR, 1), (cascade_id.WORK_FUNCTION, 1),
				(cascade_id.ROTATION_TYPE, 1), (cascade_id.TEMPERATURE_OFFSET, 5),
				(cascade_id.MINIMUM_REQUIRED_TEMPERATURE, 10), (cascade_id.MAXIMUM_REQUIRED_TEMPERATURE, 80),
			)
		}
		self.comfort_key = (101, snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT)
		self.integral_key = (102, snc.ProgramType.CASCADE_MANAGER, cascade_id.PARAM_I_FACTOR)
		self.values.update({
			self.comfort_key: 45,
			(101, snc.ProgramType.DHW, snc.DhwParameterId.WORK_MODE): 1,
			(101, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.TEMPERATURE_COMPENSATION): 5,
		})
		self.initial_values = self.values.copy()
		self.integral = 0
		self.integral_enabled = True
		self.source_power = 30
		self.frozen_power = None
		self.failed_write = None
		self.failed_read = None
		self.writes = []
		factory = patch.object(remote, 'RemoteControlParameter', side_effect=self.make_parameter)
		factory.start()
		self.addCleanup(factory.stop)
		self.scenario.wait_state_permanence = Mock(side_effect=self.wait_stable)
		self.scenario.wait_event = Mock(side_effect=self.wait_event)
		self.scenario.set_sensor_value = self.set_sensor_value

	def set_sensor_value(self, sensor, value):
		sensor.set_manual(True)
		sensor.set_value(value, True)
		if sensor not in self.scenario._manualSensorsList:
			self.scenario._manualSensorsList.append(sensor)

	def advance(self, seconds):
		# A fake response source to exercise scenario decisions, NOT a firmware
		# simulator or evidence of the actual controller's PID correctness.
		if self.values[self.integral_key] and self.integral_enabled:
			self.integral += max(0, self.values[self.comfort_key] - self.collector.get_value()) * seconds * 0.1
		else:
			self.integral = 0

	def wait_stable(self, predicate, duration, timeout):
		self.advance(duration)
		return predicate() and predicate()

	def wait_event(self, predicate, timeout):
		for _ in range(timeout):
			self.advance(1)
			if predicate():
				return True
		return False

	def make_parameter(self, *, programType, parameterId, programId, parameterIndex=None, parameterValue=None):
		key = (programId, programType, parameterId)
		parameter = Mock()
		parameter.read.side_effect = lambda: key != self.failed_read
		def read_value():
			if programType == snc.ProgramType.TEMPERATURE_SOURCE:
				return self.values[self.comfort_key]
			if parameterId == snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID and programId == 102:
				return (103, 104)[parameterIndex]
			if parameterId == snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_POWER and programId == 102:
				return self.source_power
			if parameterId == snc.CascadeManagerParameterId.REQUIRED_POWER and programId == 102:
				if self.frozen_power is not None:
					return self.frozen_power
				error = self.values[self.comfort_key] - self.collector.get_value()
				return int(max(0, min(50, 5 * error + self.integral)))
			return self.values.get(key)
		parameter.get_value.side_effect = read_value
		def write():
			self.values[key] = parameterValue
			self.writes.append((key, parameterValue))
			return (key, parameterValue) != self.failed_write
		parameter.write.side_effect = write
		return parameter

	def assert_restored(self, status='FAIL'):
		self.assertEqual(self.scenario._status, status)
		self.assertEqual(self.values, self.initial_values)
		self.assertEqual([sensor.get_value() for sensor in self.sensors], [30, 30])
		self.assertFalse(any(sensor.isManual() for sensor in self.sensors))
		self.assertEqual(self.scenario._manualSensorsList, [])

	def test_success_checks_both_temperatures_and_integration(self):
		self.scenario.run()
		self.assert_restored('OK')
		self.assertIn((self.comfort_key, 54), self.writes)
		self.assertIn((self.integral_key, Scenario.INTEGRAL_FACTOR), self.writes)
		self.assertEqual(self.scenario.get_checklist_id(), '3.6.3')
		self.assertTrue(self.scenario.force_preset_load())

	def test_fixed_power_is_rejected(self):
		self.frozen_power = 10
		self.scenario.run()
		self.assert_restored()

	def test_missing_integration_is_rejected(self):
		self.integral_enabled = False
		self.scenario.run()
		self.assert_restored()

	def test_sources_not_discovered_is_failure(self):
		self.source_power = 0
		self.scenario.run()
		self.assert_restored()

	def test_own_boiler_sensor_is_rejected_before_changes(self):
		self.programs['boiler_1'].get_input_channel.return_value.is_mapped.return_value = True
		self.scenario.run()
		self.assert_restored()
		self.assertEqual(self.writes, [])

	def test_failed_read_causes_no_changes(self):
		self.failed_read = self.integral_key
		self.scenario.run()
		self.assert_restored()
		self.assertEqual(self.writes, [])

	def test_failed_write_that_reached_controller_is_restored(self):
		self.failed_write = (self.comfort_key, 54)
		self.scenario.run()
		self.assert_restored()

	def test_partial_configuration_failure_is_restored(self):
		key = (102, snc.ProgramType.CASCADE_MANAGER, snc.CascadeManagerParameterId.PARAM_P_FACTOR)
		self.failed_write = (key, Scenario.PROPORTIONAL_BAND)
		self.scenario.run()
		self.assert_restored()

	def test_invalid_parameter_prevents_writes(self):
		for value in (None, 'UNDEF', float('nan'), float('inf')):
			with self.subTest(value=value):
				self.values[self.integral_key] = value
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assertEqual(self.writes, [])

	def test_unmapped_or_faulty_sensor_prevents_writes(self):
		for mapping, fault in ((None, False), (self.collector.get_mapping(), True)):
			with self.subTest(mapping=mapping, fault=fault):
				self.collector.set_mapping(mapping)
				self.collector.setShort(fault)
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assertEqual(self.writes, [])

	def test_external_stop_restores_everything(self):
		class Stopped(Exception):
			pass
		self.scenario.wait_event.side_effect = Stopped()
		with self.assertRaises(Stopped):
			self.scenario.run()
		self.assert_restored()

	def test_manual_state_is_preserved(self):
		self.collector.set_manual(True)
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertTrue(self.collector.isManual())
		self.assertFalse(self.dhw_sensor.isManual())
		self.assertEqual(self.collector.get_value(), 30)
		self.assertEqual(self.scenario._manualSensorsList, [])

	def test_restore_failure_does_not_skip_other_settings_or_sensors(self):
		self.failed_write = (self.comfort_key, self.initial_values[self.comfort_key])
		self.scenario.run()
		self.assert_restored()

	def test_sensor_restore_failure_does_not_skip_next_sensor(self):
		original_set_value = self.collector.set_value
		def set_value(value, manual=False):
			if value == 30:
				raise RuntimeError('sensor restore failure')
			return original_set_value(value, manual)
		self.collector.set_value = set_value
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.values, self.initial_values)
		self.assertFalse(any(sensor.isManual() for sensor in self.sensors))
		self.assertEqual(self.dhw_sensor.get_value(), 30)


if __name__ == '__main__':
	unittest.main()
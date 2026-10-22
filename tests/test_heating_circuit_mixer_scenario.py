"""Scenario orchestration and thermal-model checks; not a firmware integration test."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc
from simulator.heating_circuit import Simulator as CircuitModel


def load_scenario():
	parent = ModuleType('scenario.scenario')
	parent.Scenario = type('Parent', (), {'RELAY_MIN': 1, 'RELAY_MAX': 254, 'RELAY_ON': 255})
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	path = Path(__file__).resolve().parents[1] / 'scenario/list/heating_circuit/scenario_heating_circuit_3_3_2.py'
	spec = importlib.util.spec_from_file_location('mixer_scenario_under_test', path)
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {
		'scenario.scenario': parent,
		'smartnet.remoteControl': remote,
		'consoleLog': console,
	}):
		spec.loader.exec_module(module)
	return module


scenario_module = load_scenario()
Scenario = scenario_module.Scenario


class Channel:
	def __init__(self, value, mapped=True):
		self.value = value
		self.manual = False
		self.mapped = mapped

	def get_value(self):
		return self.value

	def set_value(self, value, manual=False):
		if not self.manual or manual:
			self.value = value

	def set_manual(self, value):
		self.manual = value

	def isManual(self):
		return self.manual

	def isShort(self):
		return False

	def isOpen(self):
		return False

	def is_mapped(self):
		return self.mapped

	def get_mapping(self):
		return self if self.mapped else None


class TestHeatingCircuitMixerScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = Scenario()
		self.clock = 0
		self.fault = None
		self.seen_cold = False
		self.inputs = {'temperature': Channel(20), 'backwardTemperature': Channel(20, False)}
		self.outputs = {'analogValve': Channel(0), 'pump': Channel(255)}
		self.boiler_sensor = Channel(30)
		self.boiler = Mock()
		self.boiler.get_id.return_value = 102
		self.boiler.get_input_channel.return_value = self.boiler_sensor
		self.circuit = Mock()
		self.circuit.get_id.return_value = 101
		self.circuit.get_input_channel.side_effect = self.inputs.__getitem__
		self.circuit.get_output_channel.side_effect = self.outputs.__getitem__
		self.circuit.get_max_flow_rate.return_value = 1000
		control = SimpleNamespace(
			getOat=lambda: None,
			_collector=SimpleNamespace(get_direct_temperature=lambda: self.boiler_sensor.value - 1),
		)
		self.model = CircuitModel(self.circuit, control)
		self.scenario._sim = SimpleNamespace(getHeatingCircuitList=lambda: [self.model])
		self.scenario._programList = {'heating_circuit': self.circuit, 'boiler': self.boiler}
		self.scenario._circuit = self.circuit
		self.scenario._boiler = self.boiler
		self.values = {
			(program.get_id(), program_type, parameter_id): value
			for program, program_type, parameter_id, value in self.scenario._settings()
		}
		for setting, original in zip(self.scenario._settings(), (0, 45, 10, 90, 0, 180, 12, 12, 45, 1, 1)):
			program, program_type, parameter_id, _ = setting
			self.values[program.get_id(), program_type, parameter_id] = original
		self.initial_values = self.values.copy()
		self.scenario._read_parameter = Mock(side_effect=self.read_parameter)
		self.scenario._write_parameter = Mock(side_effect=self.write_parameter)
		self.scenario.wait = Mock(side_effect=self.tick)
		self.scenario.wait_event = Mock(side_effect=lambda predicate, timeout: predicate())
		self.valve_percent = 0
		self.readings = []
		self.time_patch = patch.object(scenario_module, 'time', SimpleNamespace(monotonic=lambda: self.clock))
		self.time_patch.start()
		self.addCleanup(self.time_patch.stop)

	def setpoint(self):
		return self.values[101, snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE]

	def read_parameter(self, program, program_type, parameter_id):
		if (program_type, parameter_id) == (snc.ProgramType.CONSUMER, snc.ConsumerParameterId.REQUIRED_TEMPERATURE):
			return self.setpoint()
		return self.values[program.get_id(), program_type, parameter_id]

	def write_parameter(self, program, program_type, parameter_id, value):
		self.values[program.get_id(), program_type, parameter_id] = value
		return True

	def tick(self, duration):
		# Simple reference regulator matching the firmware's old analog algorithm:
		# integral opening increments every five seconds with a 1 C deadband.
		self.clock += duration
		if self.clock % 5 == 0:
			delta = self.inputs['temperature'].value - self.setpoint()
			step = 100 * 5 / Scenario.VALVE_RUNNING_TIME
			change = 0 if abs(delta) < 1 else max(-step, min(step, -delta / 10 * step))
			self.valve_percent = max(0, min(100, self.valve_percent + change))
			self.outputs['analogValve'].value = round(1 + self.valve_percent * 253 / 100)
		if self.fault == 'closed':
			self.outputs['analogValve'].value = 0
		elif self.fault == 'open':
			self.outputs['analogValve'].value = 254
		elif self.fault == 'pump_off':
			self.outputs['pump'].value = 0
		elif self.fault == 'unknown':
			self.outputs['analogValve'].value = None
		elif self.fault == 'cold_source':
			self.boiler_sensor.set_value(35, True)
		if self.boiler_sensor.value == 35:
			self.seen_cold = True
		if self.fault == 'no_recovery' and self.seen_cold:
			self.boiler_sensor.set_value(35, True)
		self.model.run()
		self.readings.append((self.boiler_sensor.value, self.setpoint(), self.outputs['analogValve'].value))
		return True

	def assert_restored(self):
		self.assertEqual(self.values, self.initial_values)
		self.assertEqual(self.boiler_sensor.value, 30)
		self.assertFalse(self.boiler_sensor.manual)

	def test_success_with_real_thermal_model_and_all_phases(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assert_restored()
		self.assertIn((35, 40, 254), self.readings)
		self.assertTrue(any(boiler == 70 and target == 50 for boiler, target, _ in self.readings))

	def test_faults_are_rejected_and_restored(self):
		for fault in ('closed', 'open', 'pump_off', 'unknown', 'cold_source'):
			with self.subTest(fault=fault):
				self.fault = fault
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_restored()

	def test_initial_read_failure_prevents_writes(self):
		self.scenario._read_parameter.return_value = None
		self.scenario._read_parameter.side_effect = None
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.scenario._write_parameter.assert_not_called()
		self.assert_restored()

	def test_write_failure_restores_partial_configuration(self):
		original = self.write_parameter
		calls = 0

		def fail_once(*args):
			nonlocal calls
			calls += 1
			return None if calls == 3 else original(*args)

		self.scenario._write_parameter.side_effect = fail_once
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_stop_exception_restores_sensor_and_parameters(self):
		self.scenario._check_phase = Mock(side_effect=RuntimeError('stopped'))
		with self.assertRaisesRegex(RuntimeError, 'stopped'):
			self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_recovery_failure_is_rejected(self):
		self.fault = 'no_recovery'
		self.scenario.run()
		self.assertTrue(self.seen_cold)
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_unconfirmed_setpoint_is_rejected(self):
		self.scenario.wait_event.return_value = False
		self.scenario.wait_event.side_effect = None
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_stabilization_must_be_continuous(self):
		self.scenario.REGULATION_TIMEOUT = 60
		self.scenario._sample = lambda: dict(
			boiler=70, source=69, flow=45 if self.clock % 20 == 0 else 40, valve=100, pump=255,
		)
		self.assertIsNone(self.scenario._check_phase('transient', 40))
		self.assertGreaterEqual(self.clock, 60)

	def test_preexisting_manual_boiler_mode_is_preserved(self):
		self.boiler_sensor.manual = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.boiler_sensor.value, 30)
		self.assertTrue(self.boiler_sensor.manual)

	def test_missing_mapping_or_model_and_manual_flow_are_rejected(self):
		self.inputs['temperature'].mapped = False
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.inputs['temperature'].mapped = True
		self.inputs['temperature'].manual = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.inputs['temperature'].manual = False
		self.scenario._sim.getHeatingCircuitList = lambda: []
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.scenario._write_parameter.assert_not_called()

	def test_cold_phase_requires_full_opening_and_actual_source_temperature(self):
		good = dict(boiler=35, source=34, flow=34, valve=254, pump=255)
		self.assertTrue(self.scenario._matches(good, 40, True, 100, 1))
		for field, value in (('valve', 150), ('flow', 20), ('source', 20), ('pump', 0), ('valve', 255), ('flow', float('nan'))):
			with self.subTest(field=field, value=value):
				self.assertFalse(self.scenario._matches(dict(good, **{field: value}), 40, True, 100, 1))
		self.assertFalse(self.scenario._matches(good, 40, False, None, 0))

	def test_restoration_error_marks_failure_and_continues_cleanup(self):
		original = self.write_parameter
		settings_count = len(self.scenario._settings())
		calls = 0

		def fail_first_restore(*args):
			nonlocal calls
			calls += 1
			if calls == settings_count + 4:
				raise RuntimeError('restore failed')
			return original(*args)

		self.scenario._write_parameter.side_effect = fail_first_restore
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(calls, settings_count * 2 + 3)
		# The failed first restore is the last configured parameter. All others
		# and the boiler sensor must still be restored.
		failed = self.scenario._settings()[-1]
		failed_key = (failed[0].get_id(), failed[1], failed[2])
		self.assertNotEqual(self.values[failed_key], self.initial_values[failed_key])
		for key, original in self.initial_values.items():
			if key != failed_key:
				self.assertEqual(self.values[key], original)
		self.assertEqual(self.boiler_sensor.value, 30)
		self.assertFalse(self.boiler_sensor.manual)


if __name__ == '__main__':
	unittest.main()
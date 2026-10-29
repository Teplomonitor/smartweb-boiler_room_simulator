"""Scenario orchestration and thermal-model checks; not a firmware integration test."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc
from simulator.heating_circuit import Simulator as CircuitModel


def load_scenario(checklist='3_3_2'):
	parent = ModuleType('scenario.scenario')
	parent.Scenario = type('Parent', (), {'RELAY_MIN': 1, 'RELAY_MAX': 254, 'RELAY_ON': 255, 'RELAY_OFF': 0})
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	root = Path(__file__).resolve().parents[1]
	base_name = 'scenario.base.heating_circuit_mixer'
	base_spec = importlib.util.spec_from_file_location(base_name, root / 'scenario/base/heating_circuit_mixer.py')
	base = importlib.util.module_from_spec(base_spec)
	path = root / f'scenario/list/heating_circuit/scenario_heating_circuit_{checklist}.py'
	spec = importlib.util.spec_from_file_location('mixer_scenario_under_test', path)
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {
		'scenario.scenario': parent,
		'smartnet.remoteControl': remote,
		'consoleLog': console,
		base_name: base,
	}):
		base_spec.loader.exec_module(base)
		spec.loader.exec_module(module)
	module.base_module = base
	return module


scenario_module = load_scenario()
Scenario = scenario_module.Scenario
three_point_module = load_scenario('3_3_3')


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
	scenario_module = scenario_module
	scenario_class = Scenario

	def setUp(self):
		self.scenario = self.scenario_class()
		self.clock = 0
		self.fault = None
		self.seen_cold = False
		self.inputs = {'temperature': Channel(20), 'backwardTemperature': Channel(20, False)}
		self.outputs = {'analogValve': Channel(0), 'pump': Channel(255)}
		self.outputs.update({name: Channel(0, False) for name in ('tptValveOpen', 'tptValveClose')})
		self.boiler_sensor = Channel(30)
		self.boiler = Mock()
		self.boiler.get_id.return_value = 102
		self.boiler.get_input_channel.return_value = self.boiler_sensor
		self.circuit = Mock()
		self.circuit.get_id.return_value = 101
		self.circuit.get_input_channel.side_effect = self.inputs.__getitem__
		self.circuit.get_output_channel.side_effect = self.outputs.__getitem__
		self.circuit.get_max_flow_rate.return_value = 1000
		self.running_time = Channel(180)
		self.circuit.get_parameters.return_value = {'valve_running_time': self.running_time}
		self.circuit.get_valve_running_time.side_effect = lambda: self.running_time.value
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
		self.time_patch = patch.object(self.scenario_module.base_module, 'time', SimpleNamespace(monotonic=lambda: self.clock))
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
		self.assertEqual(self.running_time.value, 180)

	def test_success_with_real_thermal_model_and_all_phases(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assert_restored()
		self.assertIn((35, 40, 254), self.readings)
		self.assertTrue(any(boiler == 70 and target == 50 for boiler, target, _ in self.readings))

	def test_real_sample_near_setpoint_is_accepted(self):
		self.scenario._boiler_sensor = self.boiler_sensor
		self.scenario._flow_sensor = self.inputs['temperature']
		self.scenario._pump = self.outputs['pump']
		self.scenario._model = self.model
		self.scenario._get_valve_channels()
		self.boiler_sensor.value = 70
		self.inputs['temperature'].value = 39.3
		self.outputs['analogValve'].value = 80
		self.model._valve_position = 0.3
		sample = self.scenario._sample()
		self.assertTrue(all(isinstance(value, (int, float)) for value in sample.values()))
		self.assertTrue(self.scenario._matches(sample, 40, False, None, 0))

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
			valve_open=0, valve_close=0,
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


class TestThreePointHeatingCircuitMixerScenario(TestHeatingCircuitMixerScenario):
	scenario_module = three_point_module
	scenario_class = three_point_module.Scenario

	def setUp(self):
		super().setUp()
		self.outputs['analogValve'].mapped = False
		for name in ('tptValveOpen', 'tptValveClose'):
			self.outputs[name].mapped = True
		lock_key = (101, snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.VALVE_BLOCK)
		self.values[lock_key] = self.initial_values[lock_key] = 1
		self.model._valve_update_time = 0
		self.pulse_remaining = 0
		self.pause_remaining = 0
		self.pulses = []
		model_time = patch('simulator.heating_circuit.time', SimpleNamespace(monotonic=lambda: self.clock))
		model_time.start()
		self.addCleanup(model_time.stop)

	def tick(self, duration):
		# Reference pulse regulator, not execution of the firmware. Only the
		# existing physical model integrates actuator travel and temperatures.
		self.clock += duration
		delta = self.inputs['temperature'].value - self.setpoint()
		relative = 0 if abs(delta) < 1 else delta / self.scenario.VALVE_PROPORTIONAL_BAND
		opening = closing = 0
		if abs(relative) < 0.1:
			self.pulse_remaining = self.pause_remaining = 0
		else:
			if self.pulse_remaining <= 0 and self.pause_remaining <= 0:
				self.pulse_remaining = self.scenario.VALVE_RUNNING_TIME / 30
				self.pause_remaining = 10 / abs(relative)
			if self.pulse_remaining > 0:
				opening = 255 if relative < 0 else 0
				closing = 255 if relative > 0 else 0
				self.pulse_remaining -= duration
			else:
				self.pause_remaining -= duration
		if self.fault == 'closed':
			opening, closing = 0, 255
		elif self.fault == 'open':
			opening, closing = 255, 0
		elif self.fault == 'pump_off':
			self.outputs['pump'].value = 0
		elif self.fault == 'unknown':
			opening = None
		elif self.fault == 'conflict':
			opening = closing = 255
		elif self.fault == 'invalid_relay':
			opening = 1
		elif self.fault == 'cold_source':
			self.boiler_sensor.set_value(35, True)
		if self.boiler_sensor.value == 35:
			self.seen_cold = True
		if self.fault == 'no_recovery' and self.seen_cold:
			self.boiler_sensor.set_value(35, True)
		self.outputs['tptValveOpen'].value = opening
		self.outputs['tptValveClose'].value = closing
		self.pulses.append((opening, closing))
		self.model.run()
		self.readings.append((self.boiler_sensor.value, self.setpoint(), self.model.getValveState() * 254))
		return True

	def test_unsafe_outputs_fail_immediately_and_restore(self):
		for fault in ('conflict', 'invalid_relay'):
			with self.subTest(fault=fault):
				self.fault = fault
				previous_clock = self.clock
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assertLess(self.clock - previous_clock, self.scenario.REGULATION_TIMEOUT)
				self.assert_restored()

	def test_both_directions_and_pauses_are_observed(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertTrue({(255, 0), (0, 255), (0, 0)}.issubset(self.pulses))
		self.assert_restored()

	def test_wrong_or_incomplete_mappings_prevent_writes(self):
		self.outputs['analogValve'].mapped = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.outputs['analogValve'].mapped = False
		self.outputs['tptValveClose'].mapped = False
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.scenario._write_parameter.assert_not_called()
		self.assert_restored()

	def test_invalid_model_running_time_prevents_writes(self):
		for value in (None, 0, -1, float('nan')):
			with self.subTest(value=value):
				self.running_time.value = value
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.scenario._write_parameter.assert_not_called()


if __name__ == '__main__':
	unittest.main()
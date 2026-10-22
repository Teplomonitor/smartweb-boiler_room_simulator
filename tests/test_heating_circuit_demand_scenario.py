"""Scenario orchestration with controller reply fixtures, not firmware integration."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, call, patch

import smartnet.constants as snc


ROOT = Path(__file__).resolve().parents[1]


def load_scenarios():
	parent = ModuleType('scenario.scenario')
	parent.Scenario = type('Parent', (), {})
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	name = 'scenario.base.heating_circuit_demand'
	spec = importlib.util.spec_from_file_location(name, ROOT / 'scenario/base/heating_circuit_demand.py')
	base = importlib.util.module_from_spec(spec)
	modules = []
	with patch.dict(sys.modules, {
		'scenario.scenario': parent, 'smartnet.remoteControl': remote,
		'consoleLog': console, name: base,
	}):
		spec.loader.exec_module(base)
		for index in (1, 2, 3):
			path = ROOT / f'scenario/list/heating_circuit/scenario_heating_circuit_3_3_5_{index}.py'
			spec = importlib.util.spec_from_file_location(f'demand_scenario_{index}', path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
			modules.append(module)
	return base, modules


base, modules = load_scenarios()


class TestHeatingCircuitDemandScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = modules[1].Scenario()
		self.circuit = Mock()
		self.circuit.get_id.return_value = 101
		self.room = Mock()
		self.room.get_id.return_value = 104
		self.outdoor = Mock()
		self.sensors = [Mock(), Mock()]
		for index, sensor in enumerate(self.sensors):
			sensor.get_value.return_value = (5, 21)[index]
			sensor.isManual.return_value = bool(index)
			sensor.isShort.return_value = False
			sensor.isOpen.return_value = False
			sensor.is_mapped.return_value = True
		self.outdoor.get_input_channel.return_value = self.sensors[0]
		self.room.get_input_channel.return_value = self.sensors[1]
		self.scenario._programList = {
			'heating_circuit': self.circuit, 'room': self.room,
			'outdoor': self.outdoor, 'boiler': Mock(),
		}
		self.scenario._circuit = self.circuit
		self.scenario._room = self.room
		self.scenario._outdoor_sensor, self.scenario._room_sensor = self.sensors
		self.settings = self.scenario._settings()
		self.initial = {(p.get_id(), t, i): index + 1 for index, (p, t, i, _) in enumerate(self.settings)}
		self.values = self.initial.copy()
		self.scenario._read_parameter = Mock(side_effect=lambda p, t, i: self.values[p.get_id(), t, i])
		self.scenario._write_parameter = Mock(side_effect=self.write)
		self.scenario.wait = Mock(return_value=True)

	def write(self, program, program_type, parameter_id, value):
		self.values[program.get_id(), program_type, parameter_id] = value
		return True

	def assert_restored(self, skipped=()):
		for key, value in self.initial.items():
			if key not in skipped:
				self.assertEqual(self.values[key], value)
		for index, sensor in enumerate(self.sensors):
			sensor.set_value.assert_called_with((5, 21)[index], True)
			sensor.set_manual.assert_called_with(bool(index))

	def test_all_sequences_complete_and_restore(self):
		for module in modules:
			with self.subTest(checklist=module.Scenario().get_checklist_id()):
				self.scenario.__class__ = module.Scenario
				self.scenario._check_point = Mock(return_value=36)
				self.scenario._check_integral = Mock(return_value=41.6)
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'OK')
				self.assertTrue(self.scenario._check_point.called)
				self.assert_restored()
				if self.scenario.TEST_ROOM:
					self.assertTrue(self.scenario._check_integral.called)
				else:
					self.scenario._check_integral.assert_not_called()
					for parameter_id in (snc.CircuitParameterId.ROOM_SENSOR_INFLUENCE_MIN,
						snc.CircuitParameterId.ROOM_SENSOR_INFLUENCE_MAX):
						self.assertIn(call(self.circuit, snc.ProgramType.CIRCUIT, parameter_id, 0),
							self.scenario._write_parameter.call_args_list)

	def test_fixed_outdoor_and_changed_setpoints(self):
		self.scenario._check_point = Mock()
		self.scenario._check_integral = Mock()
		self.scenario._sequence()
		self.assertTrue(all(c.args[0] == 0 for c in self.scenario._check_point.call_args_list))
		self.assertIn(call(0, 20, 22, 39.6), self.scenario._check_point.call_args_list)
		self.assertIn(call(0, 20, 18, 32.4), self.scenario._check_point.call_args_list)
		self.assertEqual(self.scenario._check_integral.call_args_list,
			[call(0, 18, 39.6), call(0, 22, 32.4)])

	def test_combined_retains_integral_when_weather_changes(self):
		self.scenario.__class__ = modules[2].Scenario
		self.scenario._check_point = Mock()
		self.scenario._check_integral = Mock(return_value=41.6)
		self.scenario._sequence()
		self.assertEqual(self.scenario._check_point.call_args_list[-2:], [
			call(0, 20, 20, 38, reset_integral=False),
			call(10, 20, 20, 30.6, reset_integral=False),
		])

	def test_invalid_sensors_prevent_writes(self):
		for value in (None, 'OPEN', float('nan'), float('inf')):
			with self.subTest(value=value):
				self.sensors[0].get_value.return_value = value
				self.scenario._run_test(Mock())
				self.assertEqual(self.scenario._status, 'FAIL')
				self.scenario._write_parameter.assert_not_called()

	def test_missing_mapping_prevents_writes(self):
		self.sensors[1].is_mapped.return_value = False
		self.scenario._run_test(Mock())
		self.assertEqual(self.scenario._status, 'FAIL')
		self.scenario._write_parameter.assert_not_called()

	def test_failed_initial_read_prevents_writes(self):
		self.scenario._read_parameter = Mock(return_value=None)
		self.scenario._run_test(Mock())
		self.assertEqual(self.scenario._status, 'FAIL')
		self.scenario._write_parameter.assert_not_called()

	def test_failed_write_restores_partial_settings(self):
		def write(*args):
			return None if self.scenario._write_parameter.call_count == 3 else self.write(*args)
		self.scenario._write_parameter.side_effect = write
		sequence = Mock()
		self.scenario._run_test(sequence)
		sequence.assert_not_called()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_failure_and_stop_restore_state(self):
		for error in (base.DemandCheckFailed('bad demand'), RuntimeError('stopped')):
			with self.subTest(error=error):
				sequence = Mock(side_effect=error)
				if isinstance(error, base.DemandCheckFailed):
					self.scenario._run_test(sequence)
				else:
					with self.assertRaisesRegex(RuntimeError, 'stopped'):
						self.scenario._run_test(sequence)
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_restored()

	def test_restore_failure_does_not_skip_other_cleanup(self):
		def write(*args):
			if self.scenario._write_parameter.call_count == len(self.settings) + 1:
				raise RuntimeError('restore failed')
			return self.write(*args)
		self.scenario._write_parameter.side_effect = write
		self.scenario._run_test(Mock())
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.scenario._write_parameter.call_count, 2 * len(self.settings))
		failed_key = (104, snc.ProgramType.ROOM_DEVICE, snc.RoomDeviceParameterId.CIRCUIT_1_SHIFT)
		self.assertEqual(self.values[failed_key], 0)
		self.assert_restored(skipped=(failed_key,))

	def test_sensor_restore_failure_does_not_skip_second_sensor(self):
		self.sensors[0].set_value.side_effect = RuntimeError('sensor failed')
		self.scenario._run_test(Mock())
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def prepare_observation(self, demand=39.6):
		readings = {
			snc.CircuitParameterId.OUTDOOR_TEMPERATURE: 0,
			snc.CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_TEMPERATURE: 18,
			snc.CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_REQUIRED_TEMPERATURE: 20,
			snc.CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_ID: 104,
		}
		self.scenario._read_parameter = Mock(side_effect=lambda p, t, i:
			readings[i] if t == snc.ProgramType.CIRCUIT else demand)
		self.scenario.wait_event = Mock(side_effect=lambda predicate, timeout: predicate())
		self.scenario.wait_state_permanence = Mock(side_effect=lambda predicate, *args: predicate())
		return readings

	def test_point_checks_actual_demand(self):
		self.prepare_observation()
		self.assertEqual(self.scenario._check_point(0, 18, 20, 39.6), 39.6)
		for demand in (None, 'UNDEF', float('nan'), 36, 43):
			self.prepare_observation(demand)
			with self.subTest(demand=demand), self.assertRaises(base.DemandCheckFailed):
				self.scenario._check_point(0, 18, 20, 39.6)

	def test_point_checks_all_controller_inputs(self):
		for parameter_id in (
			snc.CircuitParameterId.OUTDOOR_TEMPERATURE,
			snc.CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_TEMPERATURE,
			snc.CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_REQUIRED_TEMPERATURE,
			snc.CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_ID,
		):
			readings = self.prepare_observation()
			readings[parameter_id] = None
			with self.subTest(parameter_id=parameter_id), self.assertRaises(base.DemandCheckFailed):
				self.scenario._check_point(0, 18, 20, 39.6)

	def test_integral_checks_both_directions_and_rejects_faults(self):
		# Scripted replies and clock test observation logic, not controller mathematics.
		for room, baseline, final, passes in (
			(18, 39.6, 41.6, True), (22, 32.4, 30.4, True),
			(18, 39.6, 39.6, False), (22, 32.4, 34.4, False),
			(18, 39.6, None, False), (18, 39.6, 90, False),
		):
			with self.subTest(room=room, final=final):
				self.scenario._check_point = Mock(return_value=baseline)
				self.scenario._inputs_match = Mock(return_value=True)
				self.scenario._demand = Mock(return_value=final)
				with patch.object(base.time, 'monotonic', side_effect=[0, 0, 120, 120, 121]):
					if passes:
						self.assertEqual(self.scenario._check_integral(0, room, baseline), final)
					else:
						with self.assertRaises(base.DemandCheckFailed):
							self.scenario._check_integral(0, room, baseline)


if __name__ == '__main__':
	unittest.main()
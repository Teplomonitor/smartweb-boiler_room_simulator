"""Filling-loop scenario write failures without CAN or application startup."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
	spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


parent = ModuleType('scenario.scenario')
parent.Scenario = object
console = ModuleType('consoleLog')
console.print_log = Mock()
console.print_error = Mock()
with patch.dict(sys.modules, {'scenario.scenario': parent, 'consoleLog': console}):
	base = load_module('filling_loop_base_under_test', 'scenario/base/filling_loop.py')
	with patch.dict(sys.modules, {'scenario.base.filling_loop': base}):
		scenarios = [
			load_module(f'filling_loop_{number}_under_test',
				f'scenario/list/fillingLoop/scenario_filling_loop_3_13_{number}.py').Scenario
			for number in range(1, 7)
		]


class TestFillingLoopScenarios(unittest.TestCase):
	def make_scenario(self, number, failed_write=None):
		scenario = scenarios[number - 1].__new__(scenarios[number - 1])
		scenario._status = 'IN_PROGRESS'
		scenario._original_pressure_input_type = None
		scenario._test_pressure_input_type = None
		scenario._filling_loop = Mock()
		scenario._filling_loop.read_parameter_value.side_effect = (
			lambda name: 0 if name == 'pressureInputType' else 10
		)
		scenario._filling_loop.write_parameter.side_effect = (
			lambda name, value: (name, value) != failed_write
		)
		scenario.set_pressure = Mock()
		scenario.wait_state_permanence = Mock(return_value=True)
		scenario.wait_event = Mock(return_value=True)
		return scenario

	def test_rejected_pressure_input_type_fails_every_scenario(self):
		for number in range(1, 7):
			with self.subTest(scenario=number):
				scenario = self.make_scenario(number, ('pressureInputType', 1))
				scenario.run()
				self.assertEqual(scenario._status, 'FAIL')
				scenario._filling_loop.write_parameter.assert_any_call('pressureInputType', 1)

	def test_rejected_zero_reset_fails_3_13_1_even_if_relay_would_switch(self):
		scenario = self.make_scenario(1, ('autoFill', 0))
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		scenario.wait_state_permanence.assert_not_called()
		scenario._filling_loop.write_parameter.assert_any_call('autoFill', 0)

	def test_confirmed_writes_allow_3_13_1_to_pass(self):
		scenario = self.make_scenario(1)
		scenario.run()
		self.assertEqual(scenario._status, 'OK')
		scenario._filling_loop.write_parameter.assert_any_call('autoFill', 1)

	def test_cleanup_write_failure_overrides_success(self):
		scenario = self.make_scenario(1, ('pressureInputType', 0))
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		scenario._filling_loop.write_parameter.assert_any_call('pressureInputType', 0)
		scenario.set_pressure.assert_called_with('short')

	def test_duration_restore_failure_overrides_success(self):
		scenario = self.make_scenario(1, ('fillingDuration', 20))
		scenario._status = 'OK'
		scenario._original_pressure_input_type = 0
		scenario.finish_test(original_duration=20)
		self.assertEqual(scenario._status, 'FAIL')
		scenario._filling_loop.write_parameter.assert_any_call('fillingDuration', 20)
		scenario._filling_loop.write_parameter.assert_any_call('pressureInputType', 0)

	def test_cleanup_reset_failure_overrides_success(self):
		scenario = self.make_scenario(1)
		calls = 0

		def write_parameter(name, value):
			nonlocal calls
			if (name, value) == ('singleFill', 0):
				calls += 1
				return calls == 1
			return True

		scenario._filling_loop.write_parameter.side_effect = write_parameter
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(calls, 2)
		scenario._filling_loop.write_parameter.assert_any_call('pressureInputType', 0)

	def test_3_13_3_fails_if_pressure_cannot_be_restored_between_pulses(self):
		scenario = self.make_scenario(3)
		scenario.set_normal_pressure = Mock(side_effect=[True, False, True])
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		scenario.wait_event.assert_not_called()


if __name__ == '__main__':
	unittest.main()

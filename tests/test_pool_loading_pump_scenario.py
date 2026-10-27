"""Hardware-free checks for pool checklist 3.11.3 orchestration."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

from tests.alarm_scenario_helpers import Sensor


ROOT = Path(__file__).resolve().parents[1]


def load_scenario():
	def load(name, relative_path):
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
		base = load('pool_base_under_test', 'scenario/base/swimming_pool.py')
		with patch.dict(sys.modules, {'scenario.base.swimming_pool': base}):
			return load(
				'pool_loading_pump_under_test',
				'scenario/list/swimmingPool/scenario_pool_3_11_3.py',
			).Scenario


class PoolLoadingPumpScenarioTests(unittest.TestCase):
	def setUp(self):
		scenario_class = load_scenario()
		self.scenario = scenario_class.__new__(scenario_class)
		self.sensor = Sensor(23)
		self.original = {
			'workMode': 2,
			'circulationPumpWorkMode': 3,
			'requiredPoolTemperatureComfort': 27,
		}
		self.parameters = dict(self.original)
		pool = Mock()
		pool.get_temperature.return_value = self.sensor
		pool.getLoadingPumpState.return_value.is_mapped.return_value = True
		pool.getLoadingPumpState.return_value.get_value.side_effect = [0, 255, 0, 0, 255, 0]
		pool.read_parameter_value.side_effect = lambda name: self.parameters[
			'requiredPoolTemperatureComfort' if name == 'currentRequiredPoolTemperature' else name
		]

		def write_parameter(name, value):
			self.parameters[name] = value
			return 0  # Successful writes may return zero, not True.

		pool.write_parameter_value.side_effect = write_parameter
		self.scenario._pool = pool
		self.scenario.RELAY_OFF = 0
		self.scenario.set_sensor_value = lambda sensor, value: (
			sensor.set_manual(True), sensor.set_value(value, True)
		)
		self.scenario.wait_event = lambda predicate, timeout: predicate()
		self.observations = []

		def wait_state(predicate, duration, timeout):
			self.observations.append((self.sensor.value, self.parameters['requiredPoolTemperatureComfort']))
			return predicate()

		self.scenario.wait_state_permanence = Mock(side_effect=wait_state)

	def assert_restored(self):
		self.assertEqual(self.parameters, self.original)
		self.assertEqual(self.sensor.value, 23)
		self.assertFalse(self.sensor.manual)

	def test_independent_temperature_and_setpoint_sequences(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.observations, [
			(30, 28), (26, 28), (30, 28),
			(28, 26), (28, 30), (28, 26),
		])
		self.assert_restored()

	def test_each_pump_timeout_restores_state(self):
		for failed_step in range(6):
			with self.subTest(failed_step=failed_step):
				self.setUp()
				self.scenario.wait_state_permanence.side_effect = [True] * failed_step + [False]
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_restored()

	def test_failed_initial_reads_do_not_modify_parameters(self):
		for name in self.original:
			with self.subTest(parameter=name):
				self.setUp()
				self.parameters[name] = None
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.scenario._pool.write_parameter_value.assert_not_called()
				self.assertFalse(self.sensor.manual)

	def test_failed_write_restores_state(self):
		self.scenario._pool.write_parameter_value.side_effect = [0, None, 0, 0, 0]
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_missing_effective_setpoint_restores_state(self):
		read = self.scenario._pool.read_parameter_value.side_effect
		self.scenario._pool.read_parameter_value.side_effect = (
			lambda name: None if name == 'currentRequiredPoolTemperature' else read(name)
		)
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_unknown_pump_state_is_not_on_or_off(self):
		self.scenario._pool.getLoadingPumpState.return_value.get_value.side_effect = None
		self.scenario._pool.getLoadingPumpState.return_value.get_value.return_value = None
		self.assertFalse(self.scenario.check_loading_pump(False))
		self.assertFalse(self.scenario.check_loading_pump(True))

	def test_missing_sensor_mapping_fails_before_writes(self):
		self.sensor.mapped = False
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.scenario._pool.write_parameter_value.assert_not_called()

	def test_interruption_restores_state(self):
		self.scenario.wait_state_permanence.side_effect = RuntimeError('interrupted')
		with self.assertRaisesRegex(RuntimeError, 'interrupted'):
			self.scenario.run()
		self.assert_restored()


if __name__ == '__main__':
	unittest.main()
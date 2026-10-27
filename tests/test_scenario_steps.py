"""Deterministic timing tests: no real waits, transports, GUI or controller."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


def load_steps():
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	with patch.dict(sys.modules, {'consoleLog': console}):
		spec = importlib.util.spec_from_file_location('steps_under_test', Path(__file__).resolve().parents[1] / 'scenario/steps.py')
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return module


class Sensor:
	def __init__(self, value=10, manual=False, state='normal'):
		self.value, self.manual, self.state = value, manual, state
	def get_value(self): return self.value
	def isManual(self): return self.manual
	def isShort(self): return self.state == 'short'
	def isOpen(self): return self.state == 'open'
	def set_manual(self, value): self.manual = value
	def set_value(self, value, manual=False):
		if value in ('short', 'open'):
			self.state = value
		else:
			self.state, self.value = 'normal', value


class ScenarioStepsTests(unittest.TestCase):
	def setUp(self):
		self.module = load_steps()
		self.time = 0
		self.scenario = SimpleNamespace(wait=self.wait, _manualSensorsList=[], _status='IN_PROGRESS')
		self.steps = self.module.ScenarioSteps(self.scenario, clock=lambda: self.time)

	def wait(self, duration):
		self.time += duration
		return True

	def change(self, switch=5, delivered=0):
		self.steps.delayed_change('Pump', lambda: None,
			before=lambda: self.time < switch, after=lambda: self.time >= switch,
			received=lambda: self.time >= delivered, delay=5, delivery_timeout=3,
			early_tolerance=1, late_tolerance=2)

	def test_on_time_and_tolerance_boundary(self):
		self.change(switch=4)
		self.assertEqual(self.time, 4)

	def test_rejects_early_switch_even_before_receipt_confirmation(self):
		with self.assertRaisesRegex(RuntimeError, 'преждевременное'):
			self.change(switch=1, delivered=2)

	def test_rejects_late_or_missing_switch(self):
		with self.assertRaisesRegex(RuntimeError, 'вовремя'):
			self.change(switch=20)
		self.assertEqual(self.time, 7)

	def test_rejects_missing_delivery(self):
		with self.assertRaisesRegex(RuntimeError, 'не получено'):
			self.change(switch=20, delivered=20)

	def test_delivery_uncertainty_is_included_in_upper_bound(self):
		self.change(switch=8, delivered=2)
		self.assertEqual(self.time, 8)

	def test_expect_reaches_and_holds(self):
		self.steps.expect('Stable', lambda: self.time >= 2, timeout=3, hold=3)
		self.assertEqual(self.time, 5)

	def test_hold_fails_on_first_violation(self):
		with self.assertRaisesRegex(RuntimeError, 'нарушено'):
			self.steps.expect('Stable', lambda: self.time < 2, timeout=3, hold=3)

	def test_missing_state_times_out(self):
		with self.assertRaisesRegex(RuntimeError, 'тайм-аут'):
			self.steps.expect('Absent', lambda: False, timeout=2)
		self.assertEqual(self.time, 2)

	def test_slow_successful_read_cannot_bypass_timeout(self):
		def slow_read():
			self.time += 10
			return True
		with self.assertRaisesRegex(RuntimeError, 'тайм-аут'):
			self.steps.expect('Slow', slow_read, timeout=2)

	def test_late_delivery_confirmation_is_rejected(self):
		def slow_receipt():
			self.time += 10
			return True
		with self.assertRaisesRegex(RuntimeError, 'слишком поздно'):
			self.steps.delayed_change('Pump', lambda: None, before=lambda: True,
				after=lambda: False, received=slow_receipt, delay=20, delivery_timeout=3,
				early_tolerance=1, late_tolerance=2)

	def test_cancellation_restores_values_modes_faults_and_tracking(self):
		first = Sensor(manual=True)
		second = Sensor(state='open')
		with self.assertRaisesRegex(RuntimeError, 'cancel'):
			with self.module.preserved_inputs(self.scenario, [first, second]):
				for sensor in (first, second):
					sensor.set_manual(True)
					sensor.set_value(30)
					self.scenario._manualSensorsList.append(sensor)
				raise RuntimeError('cancel')
		self.assertEqual(first.value, 10)
		self.assertTrue(first.manual)
		self.assertFalse(second.manual)
		self.assertTrue(second.isOpen())
		self.assertEqual(second.value, 10)
		self.assertEqual(self.scenario._manualSensorsList, [])

	def test_cleanup_attempts_remaining_inputs_after_one_failure(self):
		first, second = Sensor(), Sensor()
		with self.assertRaisesRegex(RuntimeError, 'Не восстановлены'):
			with self.module.preserved_inputs(self.scenario, [first, second]):
				first.set_value(30)
				second.set_value = Mock(side_effect=RuntimeError('broken sensor'))
		self.assertEqual(first.value, 10)
		self.assertEqual(self.scenario._status, 'FAIL')


if __name__ == '__main__':
	unittest.main()
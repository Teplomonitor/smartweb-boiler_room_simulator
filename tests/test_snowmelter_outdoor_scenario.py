"""Checklist 3.9.3 orchestration with deterministic pump and delivery models."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tests.test_scenario_steps import Sensor, load_steps


class Input(Sensor):
	def is_mapped(self): return True


class SnowmelterOutdoorScenarioTests(unittest.TestCase):
	def setUp(self):
		self.time = 0
		steps = load_steps()
		base = ModuleType('scenario.base.snowmelter')
		base.SnowmelterScenario = object
		console = ModuleType('consoleLog')
		console.print_error = Mock()
		console.print_log = Mock()
		with patch.dict(sys.modules, {'scenario.base.snowmelter': base, 'scenario.steps': steps, 'consoleLog': console}):
			path = Path(__file__).resolve().parents[1] / 'scenario/list/snowmelter/scenario_snowmelter_3_9_3.py'
			spec = importlib.util.spec_from_file_location('snowmelter_scenario_under_test', path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
		self.module = module
		self.scenario = module.Scenario()
		self.scenario.RELAY_OFF = 0
		self.scenario.RELAY_ON = 255
		self.scenario._manualSensorsList = []
		self.scenario._status = 'IN_PROGRESS'
		self.scenario.wait = self.wait
		self.scenario.readMinOutdoorTemperature = lambda: -15
		self.scenario.readMaxOutdoorTemperature = lambda: 3
		self.scenario.readRequiredPlateTemperatureValue = lambda: 5
		self.scenario.readFrostProtectionTemperatureValue = lambda: 10
		self.outdoor, self.plate, self.backward = Input(-10, manual=True), Input(5), Input(25)
		self.sent = []
		self.off_started = None
		self.off_delay = 300
		self.cancel_at = None
		self.scenario._outdoor = SimpleNamespace(get_preset=lambda: SimpleNamespace(is_virtual=lambda: True),
			getOutdoorTemperature=lambda: self.outdoor, publish_temperature=self.publish)
		self.scenario.readSnowmelterOutdoorTemperature = lambda: self.outdoor.value
		self.scenario.setOutdoorTemperature = lambda value: self.set_sensor(self.outdoor, value)
		self.scenario.setPlateTemperature = lambda value: self.set_sensor(self.plate, value)
		self.scenario.setBacwardFlowTemperature = lambda value: self.set_sensor(self.backward, value)
		self.circulation = SimpleNamespace(is_mapped=lambda: True, get_value=self.pump_state)
		self.analog = SimpleNamespace(is_mapped=lambda: True, get_value=lambda: 0 if self.pump_state() == 0 else 100)
		self.discrete = SimpleNamespace(is_mapped=lambda: False, get_value=lambda: None)
		self.scenario._snowmelter = SimpleNamespace(getSecondaryPumpState=lambda: self.circulation,
			getPrimaryPumpState=lambda: self.discrete, getAnalogPumpSignal=lambda: self.analog,
			getPlateTemperature=lambda: self.plate, getBackwardFlowTemperature=lambda: self.backward)
		self.clock = patch.object(steps.time, 'monotonic', side_effect=lambda: self.time)
		self.clock.start()
		self.addCleanup(self.clock.stop)

	def set_sensor(self, sensor, value):
		sensor.set_manual(True)
		sensor.set_value(value, True)
		if sensor not in self.scenario._manualSensorsList:
			self.scenario._manualSensorsList.append(sensor)

	def publish(self, force=False):
		self.sent.append(self.outdoor.value)
		self.off_started = self.time if self.outdoor.value < -15 or self.outdoor.value > 3 else None

	def pump_state(self):
		return 0 if self.off_started is not None and self.time - self.off_started >= self.off_delay else 255

	def wait(self, duration):
		self.time += duration
		if self.cancel_at is not None and self.time >= self.cancel_at:
			raise InterruptedError('cancelled')
		return True

	def assert_restored(self):
		self.assertEqual((self.outdoor.value, self.plate.value, self.backward.value), (-10, 5, 25))
		self.assertTrue(self.outdoor.manual)
		self.assertFalse(self.plate.manual)
		self.assertFalse(self.backward.manual)
		self.assertEqual(self.scenario._manualSensorsList, [])

	def test_both_boundaries_and_analog_output(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.sent, [-6, 8, -6, -20])
		self.assertGreaterEqual(self.time, 1200)
		self.assert_restored()

	def test_early_and_late_shutdown_fail_and_restore(self):
		for delay in (1, 400):
			with self.subTest(delay=delay):
				self.off_delay = delay
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_restored()

	def test_cancellation_restores_inputs(self):
		self.cancel_at = 10
		with self.assertRaises(InterruptedError):
			self.scenario.run()
		self.assert_restored()

	def test_missing_parameters_do_not_modify_inputs(self):
		self.scenario.readMaxOutdoorTemperature = lambda: None
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.sent, [])
		self.assert_restored()

	def test_unknown_pump_state_fails(self):
		self.circulation.get_value = lambda: None
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()


if __name__ == '__main__':
	unittest.main()
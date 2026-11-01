"""Real program/simulator objects with a mocked bus; no application threads."""

import importlib
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class VirtualOutdoorRuntimeTests(unittest.TestCase):
	def setUp(self):
		# Preserve the application's existing import order (message/mainThread are cyclic).
		importlib.import_module('mainThread')
		self.factory = importlib.import_module('programs.factory')
		self.runtime = importlib.import_module('simulator.simulator')
		self.oat_model = importlib.import_module('simulator.oat')
		self.virtual = importlib.import_module('programs.virtual_outdoor')
		self.presets = importlib.import_module('presets.list.snowmelter_virtual_outdoor')
		self.programs = self.presets.get_presets_list()[0]
		self.preset = next(program for program in self.programs if program.is_virtual())
		self.source = self.factory.createProgram(self.preset)
		self.addCleanup(self.source.clear)
		self.bus = Mock()
		transport = patch.object(self.virtual, 'CanBusInterface')
		transport.start().return_value.get.return_value = self.bus
		self.addCleanup(transport.stop)
		# Bypass the singleton/thread constructor: exercise methods without starting services.
		self.simulator = threading.Thread.__new__(self.runtime.Simulator)
		self.simulator._state_lock = threading.RLock()
		self.simulator._clear_state()
		self.model = self.oat_model.Simulator(self.source, self.simulator)
		self.simulator._simList = [self.model]
		self.simulator._simulator_ready = True

	def test_factory_and_model_publish_manual_temperature(self):
		sensor = self.source.getOutdoorTemperature()
		self.assertTrue(sensor.is_mapped())
		sensor.set_manual(True)
		sensor.set_value(-20, True)
		self.simulator.runProgramSimulators()
		self.assertEqual(sensor.get_value(), -20)
		frame = self.bus.send.call_args.args[0]
		self.assertEqual(bytes(frame.data), b'\x38\xff')

	def test_clear_closes_source_and_removes_it_from_next_tick(self):
		self.simulator.runProgramSimulators()
		self.bus.reset_mock()
		self.simulator.clear()
		self.simulator.runProgramSimulators()
		self.source.publish_temperature(force=True)
		self.assertEqual(self.simulator._simList, [])
		self.bus.send.assert_not_called()

	def test_physical_sensor_reporter_skips_virtual_input(self):
		reporter = threading.Thread.__new__(self.runtime.sensor_report_thread)
		reporter._simulator = self.simulator
		with patch.object(self.runtime.ssr, 'reportSensorValue') as report:
			reporter.reportSensorsValues()
			report.assert_not_called()

	def test_real_and_virtual_presets_validate_without_changing_original(self):
		from presets.preset import validate_program_presets
		from presets.list.snowmelter import get_presets_list
		validate_program_presets(self.programs)
		self.assertEqual(sum(program.is_virtual() for program in self.programs), 1)
		self.assertFalse(any(program.is_virtual() for program in get_presets_list()[0]))

	def make_scenario(self):
		from scenario.scenario import Scenario
		self.source.clear()
		self.simulator._simList = []
		self.simulator._oat = None
		scenario = object.__new__(Scenario)
		scenario._controllerHost = Mock()
		scenario._controllerHost.get_virtual_outdoor_preset.return_value = self.preset
		scenario._controllerHost.get_program_list.return_value = []
		scenario._virtual_outdoor = None
		scenario._sim = self.simulator
		scenario._manualSensorsList = []
		self.addCleanup(scenario._remove_virtual_outdoor)
		return scenario

	def test_scenario_source_is_removed_and_recreated(self):
		from smartnet.message import CanListener
		scenario = self.make_scenario()
		for temperature in (15, 0):
			scenario._activate_virtual_outdoor()
			source = scenario._virtual_outdoor
			self.assertIn(source, CanListener._listeners)
			self.assertEqual(scenario.get_program_list(), [source])
			scenario.set_sensor_value(source.getOutdoorTemperature(), temperature)
			frame = self.bus.send.call_args.args[0]
			self.assertEqual(int.from_bytes(frame.data, 'little', signed=True), temperature * 10)
			scenario.clear()
			self.assertNotIn(source, CanListener._listeners)
			self.assertIsNone(self.simulator.getOat())
			self.bus.reset_mock()
			self.simulator.runProgramSimulators()
			source.publish_temperature(force=True)
			self.bus.send.assert_not_called()

	def test_simulator_failure_is_reported_to_scenario(self):
		scenario = self.make_scenario()
		scenario._activate_virtual_outdoor()
		self.bus.send.side_effect = RuntimeError('transport failure')
		self.simulator.runProgramSimulators()
		with self.assertRaisesRegex(RuntimeError, 'transport failure'):
			scenario.delay_with_break_check(0)
		self.assertTrue(self.simulator._simulator_ready)

	def test_activation_failure_unsubscribes_source(self):
		from smartnet.message import CanListener
		scenario = self.make_scenario()
		self.simulator._simulator_ready = False
		listeners = list(CanListener._listeners)
		with self.assertRaisesRegex(RuntimeError, 'Cannot attach'):
			scenario._activate_virtual_outdoor()
		self.assertEqual(CanListener._listeners, listeners)
		self.assertIsNone(scenario._virtual_outdoor)

	def test_subclass_constructor_failure_removes_source(self):
		from scenario import scenario as scenarios
		from smartnet.message import CanListener
		fixture = self.make_scenario()
		listeners = list(CanListener._listeners)
		class BrokenScenario(scenarios.Scenario):
			def __init__(self, controller, simulator):
				super().__init__(controller, simulator)
				raise RuntimeError('subclass failure')
		thread = object.__new__(scenarios.ScenarioThread)
		thread._controllerHost = fixture._controllerHost
		thread._simulator = self.simulator
		thread._progress_callback = None
		def setup(instance):
			instance._activate_virtual_outdoor()
		with (patch.object(scenarios, 'importfile', return_value=SimpleNamespace(Scenario=BrokenScenario)),
				patch.object(scenarios, 'ScenarioThread') as scenario_thread,
				patch.object(scenarios.Scenario, 'init_scenario', setup)):
			scenario_thread.return_value.getStopScenarioEvent.return_value = threading.Event()
			with self.assertRaisesRegex(RuntimeError, 'subclass failure'):
				thread.get_scenario_object('broken.py')
		self.assertEqual(CanListener._listeners, listeners)
		self.assertIsNone(self.simulator.getOat())


if __name__ == '__main__':
	unittest.main()
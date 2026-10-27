"""Real program/simulator objects with a mocked bus; no application threads."""

import importlib
import threading
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


if __name__ == '__main__':
	unittest.main()
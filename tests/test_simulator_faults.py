"""Thermal runtime regressions without services, hardware or network access."""

import importlib
import math
import threading
import unittest
from unittest.mock import Mock, patch


class SimulatorFaultTests(unittest.TestCase):
	def setUp(self):
		importlib.import_module('mainThread')
		self.runtime = importlib.import_module('simulator.simulator')
		self.snowmelter = importlib.import_module('simulator.snowmelter')
		read_output = patch('programs.program.Program.read_output')
		read_output.start()
		self.addCleanup(read_output.stop)
		self.simulator = threading.Thread.__new__(self.runtime.Simulator)
		self.simulator._state_lock = threading.RLock()
		self.simulator._clear_state()
		self.simulator._simulator_ready = True

	def test_missing_outdoor_sensor_returns_zero(self):
		model = object.__new__(self.snowmelter.Simulator)
		model._control = Mock()
		model._control.getOat.return_value = None
		self.assertEqual(model.getOat(), 0)

	def test_existing_outdoor_sensor_temperature_is_used(self):
		model = object.__new__(self.snowmelter.Simulator)
		model._control = Mock()
		model._control.getOat.return_value.get_temperature.return_value = -12.5
		self.assertEqual(model.getOat(), -12.5)

	def test_heat_dump_models_run_without_outdoor_sensor(self):
		from presets.list.heat_dump import get_presets_list
		from programs.factory import createProgram
		from smartnet.constants import ProgramType
		presets, _ = get_presets_list()
		self.assertNotIn(ProgramType.OUTDOOR_SENSOR, [p.get_type() for p in presets])
		for preset in presets:
			program = createProgram(preset)
			self.addCleanup(program.clear)
			model = self.runtime.simulatorType[program.get_type()](program, self.simulator)
			self.simulator._simList.append(model)
		self.simulator._consumersList = [model for model in self.simulator._simList
			if model._program.get_type() in self.runtime.consumerTypesList]
		self.simulator._heatingCircuitList = [model for model in self.simulator._simList
			if model._program.get_type() == ProgramType.HEATING_CIRCUIT]
		self.simulator._collector = self.runtime.simulator.collector.Simulator(self.simulator)
		for _ in range(3):
			for model in self.simulator._simList:
				model.run()  # Do not let the runtime exception handler hide a regression.
			self.simulator.runCollector()
		snow = next(model for model in self.simulator._simList
			if model._program.get_type() == ProgramType.SNOWMELT)
		self.assertTrue(math.isfinite(snow.getPlateTemperature()))
		self.assertNotEqual(snow.getPlateTemperature(), -5)

	def make_faulty_model(self, virtual=False):
		model = Mock()
		model._program.get_id.return_value = 102
		model._program.get_type.return_value = 'SNOWMELT'
		model._program.get_preset.return_value.is_virtual.return_value = virtual
		model.run.side_effect = ValueError('bad temperature')
		self.simulator._simList = [model]
		return model

	def test_fault_is_identified_deduplicated_and_recovery_reported(self):
		model = self.make_faulty_model()
		healthy = Mock()
		self.simulator._simList.append(healthy)
		with patch.object(self.runtime, 'print_error') as error_log, \
			patch.object(self.runtime, 'print_log') as recovery_log:
			self.simulator.runProgramSimulators()
			self.simulator.runProgramSimulators()
			error_log.assert_called_once()
			message = error_log.call_args.args[0]
			for text in ('102', 'SNOWMELT', 'ValueError', 'bad temperature', 'Traceback'):
				self.assertIn(text, message)
			self.assertEqual(healthy.run.call_count, 2)
			model.run.side_effect = None
			self.simulator.runProgramSimulators()
			self.simulator.runProgramSimulators()
			recovery_log.assert_called_once()
			model.run.side_effect = ValueError('bad temperature')
			self.simulator.runProgramSimulators()
			self.assertEqual(error_log.call_count, 2)

	def test_changed_error_is_logged_and_clear_resets_faults(self):
		model = self.make_faulty_model()
		with patch.object(self.runtime, 'print_error') as error_log:
			self.simulator.runProgramSimulators()
			model.run.side_effect = TypeError('different error')
			self.simulator.runProgramSimulators()
			self.assertEqual(error_log.call_count, 2)
			self.simulator.clear()
			self.assertEqual(self.simulator._program_simulator_faults, {})

	def test_virtual_publish_error_still_uses_program_handler(self):
		model = self.make_faulty_model(virtual=True)
		with patch.object(self.runtime, 'print_error') as error_log:
			self.simulator.runProgramSimulators()
			self.simulator.runProgramSimulators()
			error_log.assert_not_called()
		self.assertEqual(model._program.record_publish_error.call_count, 2)


if __name__ == '__main__':
	unittest.main()

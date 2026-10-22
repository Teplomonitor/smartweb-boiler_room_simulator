"""Mixer actuator and thermal-model tests without GUI, CAN or a controller."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from simulator.heating_circuit import Simulator


class Channel:
	def __init__(self, value=0, mapped=True):
		self.value = value
		self.mapped = mapped

	def get_value(self):
		return self.value

	def set_value(self, value):
		self.value = value

	def get_mapping(self):
		return self if self.mapped else None


class TestHeatingCircuitValve(unittest.TestCase):
	def setUp(self):
		self.clock = 0.0
		clock_patch = patch('simulator.heating_circuit.time.monotonic', side_effect=lambda: self.clock)
		clock_patch.start()
		self.addCleanup(clock_patch.stop)
		log_patch = patch('simulator.heating_circuit.print_error')
		self.log = log_patch.start()
		self.addCleanup(log_patch.stop)
		self.inputs = {name: Channel(20) for name in ('temperature', 'backwardTemperature')}
		self.outputs = {
			'analogValve': Channel(127, False),
			'tptValveOpen': Channel(),
			'tptValveClose': Channel(),
			'pump': Channel(255),
		}
		self.program = Mock()
		self.program.get_id.return_value = 101
		self.program.get_input_channel.side_effect = self.inputs.__getitem__
		self.program.get_output_channel.side_effect = self.outputs.__getitem__
		self.program.get_valve_running_time.return_value = 120
		self.program.get_max_flow_rate.return_value = 1000
		self.program.get_max_power.return_value = 3
		control = SimpleNamespace(getOat=lambda: None,
			_collector=SimpleNamespace(get_direct_temperature=lambda: 80))
		self.model = Simulator(self.program, control)

	def advance(self, seconds, opening=0, closing=0):
		self.outputs['tptValveOpen'].value = opening
		self.outputs['tptValveClose'].value = closing
		self.clock += seconds
		self.model.run()
		return self.model.getValveState()

	def test_initial_position_and_time_integration(self):
		self.assertEqual(self.model.getValveState(), 0)
		self.assertAlmostEqual(self.advance(30, opening=255), 0.25)
		self.assertAlmostEqual(self.advance(30, opening=255), 0.5)
		self.assertAlmostEqual(self.advance(15, closing=255), 0.375)
		self.assertAlmostEqual(self.advance(120), 0.375)

	def test_full_travel_and_end_switches(self):
		self.assertEqual(self.advance(120, opening=255), 1)
		self.assertEqual(self.advance(600, opening=255), 1)
		self.assertEqual(self.advance(120, closing=255), 0)
		self.assertEqual(self.advance(600, closing=255), 0)
		self.assertEqual(self.advance(180, opening=255), 1)

	def test_continuous_full_travel_synchronizes_any_initial_position(self):
		for initial in (0, 0.2, 0.8, 1):
			with self.subTest(initial=initial):
				self.model._valve_position = initial
				self.assertEqual(self.advance(120, opening=255), 1)
				self.model._valve_position = initial
				self.assertEqual(self.advance(120, closing=255), 0)

	def test_getters_do_not_integrate_and_zero_elapsed_does_not_move(self):
		self.advance(60, opening=255)
		self.clock += 30
		for _ in range(10):
			self.assertEqual(self.model.getValveState(), 0.5)
			self.assertEqual(self.model.get_flow(), 0.5)
			self.assertEqual(self.model.get_power(), 1.5)
		self.model.run()
		self.assertEqual(self.advance(0, opening=255), 0.75)

	def test_thermal_model_uses_estimated_position(self):
		self.advance(60, opening=255)
		self.assertEqual(self.model.get_temperature(), 50)
		self.assertAlmostEqual(self.model.get_backward_temperature(),
			self.model.get_backward_temperature2() * 0.5 + 80 * 0.5)
		self.assertEqual(self.model.get_flow(), 0.5)
		self.assertEqual(self.model.get_power(), 1.5)

	def test_actuator_moves_with_pump_off(self):
		self.outputs['pump'].value = 0
		self.assertEqual(self.advance(60, opening=255), 0.5)
		self.assertEqual(self.model.get_flow(), 0)
		self.assertEqual(self.model.get_power(), 0)

	def test_running_time_can_be_changed(self):
		self.program.get_valve_running_time.return_value = 60
		self.assertEqual(self.advance(30, opening=255), 0.5)
		self.program.get_valve_running_time.return_value = 240
		self.assertEqual(self.advance(60, opening=255), 0.75)

	def test_invalid_running_time_holds_position(self):
		for value in (None, 0, -1, float('nan'), float('inf')):
			with self.subTest(value=value):
				self.program.get_valve_running_time.return_value = value
				self.assertEqual(self.advance(60, opening=255), 0)
		self.program.get_valve_running_time.return_value = 120
		self.assertEqual(self.advance(60, opening=255), 0.5)

	def test_conflict_holds_position_and_logs_once_per_episode(self):
		self.advance(60, opening=255)
		for _ in range(3):
			self.assertEqual(self.advance(60, opening=255, closing=255), 0.5)
		self.log.assert_called_once()
		self.assertIn('101', self.log.call_args.args[0])
		self.advance(10)
		self.advance(60, opening=255, closing=255)
		self.assertEqual(self.log.call_count, 2)
		self.assertEqual(self.advance(30, closing=255), 0.25)

	def test_analog_has_priority_even_with_conflict(self):
		self.outputs['analogValve'].mapped = True
		for value, expected in ((0, 0), (127, 0.5), (254, 1), (None, 1)):
			with self.subTest(value=value):
				self.outputs['analogValve'].value = value
				self.assertEqual(self.advance(120, opening=255, closing=255), expected)
		self.log.assert_called_once()
		self.assertEqual(self.model._valve_position, 0)
		self.program.get_valve_running_time.assert_not_called()

	def test_analog_does_not_accumulate_three_point_travel(self):
		self.outputs['analogValve'].mapped = True
		self.advance(600, opening=255)
		self.outputs['analogValve'].mapped = False
		self.assertEqual(self.advance(30, opening=255), 0.25)

	def test_unknown_values_and_incomplete_mapping_hold_position(self):
		self.advance(60, opening=255)
		for opening, closing in ((None, 0), (255, None), (None, None)):
			self.assertEqual(self.advance(60, opening, closing), 0.5)
		for name in ('tptValveOpen', 'tptValveClose'):
			self.outputs[name].mapped = False
			self.assertEqual(self.advance(60, opening=255), 0.5)
			self.outputs[name].mapped = True
		self.log.assert_not_called()
		self.assertEqual(self.advance(30, opening=255), 0.75)

	def test_no_actuator_mappings_preserves_fully_open_behavior(self):
		for output in ('tptValveOpen', 'tptValveClose'):
			self.outputs[output].mapped = False
		self.assertEqual(self.advance(120, opening=255), 1)


class TestValveRunningTimeParameter(unittest.TestCase):
	def test_default_and_editable_parameter(self):
		parent = ModuleType('programs.program')
		parent.Program = object
		parent.input_info = Mock()
		parent.output_info = Mock()
		gui = ModuleType('gui.parameter')
		gui.GuiParameter = Mock(side_effect=lambda value, *args: Channel(value))
		path = Path(__file__).resolve().parents[1] / 'programs/heating_circuit.py'
		spec = importlib.util.spec_from_file_location('programs.valve_model_test', path)
		module = importlib.util.module_from_spec(spec)
		with patch.dict(sys.modules, {'programs.program': parent, 'gui.parameter': gui}):
			spec.loader.exec_module(module)
		program = module.HeatingCircuit.__new__(module.HeatingCircuit)
		program._parameters = {}
		program.init_gui_parameters()
		self.assertEqual(program.get_valve_running_time(), 120)
		self.assertEqual(gui.GuiParameter.call_args.args[2:], (1, 3600, 1, 'с'))
		program._parameters['valve_running_time'].set_value(180)
		self.assertEqual(program.get_valve_running_time(), 180)


if __name__ == '__main__':
	unittest.main()
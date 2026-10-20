"""Boiler power model tests without GUI, CAN or an external controller."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc
from simulator.boiler import Simulator
from simulator.collector import Simulator as CollectorSimulator
from simulator.heating_circuit import Simulator as CircuitSimulator


def load_boiler_model():
	parent = ModuleType('programs.program')
	parent.Program = object
	parent.input_info = Mock()
	parent.output_info = Mock()
	gui = ModuleType('gui.parameter')
	gui.GuiParameter = Mock()
	path = Path(__file__).resolve().parents[1] / 'programs/boiler.py'
	spec = importlib.util.spec_from_file_location('programs.boiler_modulation_test', path)
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {'programs.program': parent, 'gui.parameter': gui}):
		spec.loader.exec_module(module)
	return module.Boiler


Boiler = load_boiler_model()


class TestBoilerModulation(unittest.TestCase):
	def setUp(self):
		self.output = Mock()
		self.output.is_mapped.return_value = True
		self.output.get_value.return_value = 0
		self.stage = Mock()
		self.stage.is_mapped.return_value = False
		self.stage.get_value.return_value = 0
		self.sensor = Mock()
		self.sensor.get_value.side_effect = lambda: self.temperature
		self.sensor.set_value.side_effect = lambda value: setattr(self, 'temperature', value)
		self.program = Mock()
		self.program.get_preset.return_value = None
		self.program.get_power_output.return_value = self.output
		self.program.get_stage_1.return_value = self.stage
		self.program.get_stage_1_power_percent.return_value = 50
		self.program.get_max_power.return_value = 30
		self.program.get_max_flow_rate.return_value = 3000
		self.program.get_power_output_percent.side_effect = lambda: Boiler.get_power_output_percent(self.program)
		self.program.get_temperature.side_effect = self.sensor.get_value
		self.program.set_temperature.side_effect = self.sensor.set_value
		self.control = Mock()
		self.control._collector.get_supply_backward_temperature.return_value = 30
		self.simulator = Simulator(self.program, self.control)

	def test_signal_conversion_and_missing_mapping(self):
		for signal, expected in ((None, None), (0, 0), (1, 0), (127, 12600 / 253), (254, 100), (255, 100)):
			with self.subTest(signal=signal):
				self.output.get_value.return_value = signal
				actual = Boiler.get_power_output_percent(self.program)
				if expected is None:
					self.assertIsNone(actual)
				else:
					self.assertAlmostEqual(actual, expected)
		self.output.is_mapped.return_value = False
		self.assertIsNone(Boiler.get_power_output_percent(self.program))

	def test_only_analog_stage_controls_entire_power(self):
		for signal, expected in ((0, 0), (1, 0), (127, 30 * 126 / 253), (254, 30), (255, 30), (None, 0)):
			with self.subTest(signal=signal):
				self.output.get_value.return_value = signal
				self.simulator.compute_power()
				self.assertAlmostEqual(self.simulator.get_power(), expected)

	def test_mixed_stages_have_independent_contributions(self):
		self.stage.is_mapped.return_value = True
		for share in (0, 25, 50, 100):
			self.program.get_stage_1_power_percent.return_value = share
			for first in (0, 255):
				self.stage.get_value.return_value = first
				for signal in (None, 0, 127, 254):
					with self.subTest(share=share, first=first, signal=signal):
						self.output.get_value.return_value = signal
						fraction = 0 if signal is None else max(0, (signal - 1) / 253)
						expected = 30 * ((share / 100 if first else 0) + (1 - share / 100) * fraction)
						self.simulator.compute_power()
						self.assertAlmostEqual(self.simulator.get_power(), expected)

	def test_overheat_protection_still_disables_analog_power(self):
		self.output.get_value.return_value = 254
		self.simulator._boilerOverheatDelay = Mock()
		self.simulator._boilerOverheatDelay.get.return_value = True
		self.simulator.compute_power()
		self.assertEqual(self.simulator.get_power(), 0)

	def test_power_changes_temperature_instead_of_a_hidden_thermostat(self):
		self.output.get_value.return_value = 0
		self.simulator.compute_power()
		cold = self.simulator.compute_temperature()
		self.output.get_value.return_value = 254
		self.simulator.compute_power()
		hot = self.simulator.compute_temperature()
		self.assertLess(cold, self.temperature)
		self.assertGreater(hot, self.temperature)
		self.assertLessEqual(hot - self.temperature, 1)

	def test_legacy_discrete_mode_ramps_without_negative_power(self):
		self.output.is_mapped.return_value = False
		self.stage.is_mapped.return_value = True
		self.stage.get_value.return_value = 255
		self.simulator.compute_power()
		self.assertAlmostEqual(self.simulator.get_power(), 0.05)
		self.stage.get_value.return_value = 0
		for _ in range(3):
			self.simulator.compute_power()
			self.assertEqual(self.simulator.get_power(), 0)

	def test_legacy_unmapped_burner_keeps_default_behavior(self):
		self.output.is_mapped.return_value = False
		self.simulator.compute_power()
		self.assertAlmostEqual(self.simulator.get_power(), 0.05)

	def test_standard_power_can_heat_one_fully_open_consumer(self):
		consumer_program = Mock()
		consumer_program.get_max_flow_rate.return_value = 1000
		consumer_program.get_max_power.return_value = 3
		channels = {}
		for name in ('temperature', 'backwardTemperature'):
			channel = Mock()
			channel.get_value.side_effect = lambda name=name: channels[name].value
			channel.set_value.side_effect = lambda value, name=name: setattr(channels[name], 'value', value)
			channels[name] = channel
		consumer_program.get_input_channel.side_effect = channels.__getitem__
		consumer_program.get_output_channel.return_value.get_value.return_value = 254
		self.control.getOat.return_value = None
		consumer = CircuitSimulator(consumer_program, self.control)
		self.program.get_type.return_value = snc.ProgramType.BOILER
		self.control.getSourceList.return_value = [self.simulator]
		self.control.getConsumerList.return_value = [consumer]
		self.control._collector = CollectorSimulator(self.control)
		self.output.get_value.return_value = 254

		def thermal_step():
			consumer.run()
			self.simulator.run()
			self.control._collector.run()

		# Advance model ticks without real-time waits or a fabricated controller.
		for _ in range(200):
			thermal_step()
			if self.temperature >= 60:
				break
		self.assertGreaterEqual(self.temperature, 60)
		hot = self.temperature
		self.output.get_value.return_value = 0
		for _ in range(60):
			thermal_step()
		self.assertLess(self.temperature, hot - 5)


if __name__ == '__main__':
	unittest.main()
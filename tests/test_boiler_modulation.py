"""Boiler power model tests without GUI, CAN or an external controller."""

import importlib.util
from itertools import product
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
		self.stage_2 = Mock()
		self.stage_2.is_mapped.return_value = False
		self.stage_2.get_value.return_value = 0
		self.sensor = Mock()
		self.sensor.get_value.side_effect = lambda: self.temperature
		self.sensor.set_value.side_effect = lambda value: setattr(self, 'temperature', value)
		self.program = Mock()
		self.program.get_preset.return_value = None
		self.program.get_power_output.return_value = self.output
		self.program.get_stage_1.return_value = self.stage
		self.program.get_stage_2.return_value = self.stage_2
		self.program.get_stage_1_power.return_value = 30
		self.program.get_stage_2_power.return_value = 30
		self.program.get_analog_power.return_value = 30
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
		self.stage_2.is_mapped.return_value = True
		self.program.get_stage_2_power.return_value = 0.3
		self.program.get_analog_power.return_value = 17
		for power, first, second, signal in product((0, 0.1, 0.2), (0, 255), (0, 255), (None, 0, 127, 254)):
			with self.subTest(power=power, first=first, second=second, signal=signal):
				self.program.get_stage_1_power.return_value = power
				self.stage.get_value.return_value = first
				self.stage_2.get_value.return_value = second
				self.output.get_value.return_value = signal
				fraction = 0 if signal is None else max(0, (signal - 1) / 253)
				expected = (power if first else 0) + (0.3 if second else 0) + 17 * fraction
				for _ in range(12):
					self.simulator.compute_power()
				self.assertAlmostEqual(self.simulator.get_power(), expected)

	def test_all_mapping_combinations_ignore_unmapped_signals(self):
		self.program.get_stage_1_power.return_value = 0.1
		self.program.get_stage_2_power.return_value = 0.2
		self.program.get_analog_power.return_value = 7
		for mappings in product((False, True), repeat=3):
			with self.subTest(mappings=mappings):
				for channel, mapped in zip((self.stage, self.stage_2, self.output), mappings):
					channel.is_mapped.return_value = mapped
					channel.get_value.return_value = 255
				for _ in range(8):
					self.simulator.compute_power()
				self.assertAlmostEqual(self.simulator.get_power(), sum(
					power for power, mapped in zip((0.1, 0.2, 7), mappings) if mapped))

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

	def test_unmapped_burners_do_not_heat(self):
		self.output.is_mapped.return_value = False
		self.stage.get_value.return_value = 255
		self.stage_2.get_value.return_value = 255
		self.simulator.compute_power()
		self.assertEqual(self.simulator.get_stage_state(), 0)
		self.assertEqual(self.simulator.get_power(), 0)

	def test_discrete_ramp_is_preserved_in_mixed_mode(self):
		self.stage.is_mapped.return_value = True
		self.stage.get_value.return_value = 255
		self.output.get_value.return_value = 254
		for expected in (30.05, 30.1, 30.15):
			self.simulator.compute_power()
			self.assertAlmostEqual(self.simulator.get_power(), expected)
		self.output.get_value.return_value = 0
		self.simulator.compute_power()
		self.assertAlmostEqual(self.simulator.get_power(), 0.2)
		self.stage.get_value.return_value = 0
		self.simulator.compute_power()
		self.assertEqual(self.simulator.get_power(), 0)

	def test_overheat_ramps_down_discrete_and_disables_analog(self):
		self.stage.is_mapped.return_value = True
		self.stage_2.is_mapped.return_value = True
		self.stage.get_value.return_value = 255
		self.stage_2.get_value.return_value = 255
		self.output.get_value.return_value = 254
		for _ in range(20):
			self.simulator.compute_power()
		self.simulator._boilerOverheatDelay = Mock()
		self.simulator._boilerOverheatDelay.get.return_value = True
		self.simulator.compute_power()
		self.assertAlmostEqual(self.simulator.get_power(), 0.5)
		for _ in range(3):
			self.simulator.compute_power()
		self.assertEqual(self.simulator.get_power(), 0)

	def test_discrete_power_reaches_configured_sum(self):
		self.stage.is_mapped.return_value = True
		self.stage_2.is_mapped.return_value = True
		self.stage.get_value.return_value = 255
		self.stage_2.get_value.return_value = 255
		for _ in range(1201):
			self.simulator.compute_power()
		self.assertAlmostEqual(self.simulator.get_power(), 60)
		self.stage.get_value.return_value = 0
		for _ in range(61):
			self.simulator.compute_power()
		self.assertAlmostEqual(self.simulator.get_power(), 30)

	def test_zero_analog_power(self):
		self.program.get_analog_power.return_value = 0
		self.output.get_value.return_value = 254
		self.simulator.compute_power()
		self.assertEqual(self.simulator.get_power(), 0)

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


class TestBoilerPowerParameters(unittest.TestCase):
	def setUp(self):
		self.boiler = Boiler.__new__(Boiler)
		self.boiler._parameters = {}
		self.factory = Mock(side_effect=lambda value, *args: Mock(get_value=Mock(return_value=value)))
		with patch.dict(Boiler.init_gui_parameters.__globals__, {'GuiParameter': self.factory}):
			self.boiler.init_gui_parameters()
		self.channels = {name: Mock() for name in ('burner1', 'burner2', 'power')}
		self.boiler.get_output_channel = self.channels.__getitem__

	def test_defaults_and_gui_units(self):
		self.assertEqual(set(self.boiler._parameters), {
			'max_flow_rate', 'stage_1_power', 'stage_2_power', 'analog_power',
		})
		for args in self.factory.call_args_list[1:]:
			self.assertEqual(args.args[0], 30)
			self.assertEqual(args.args[2:], (0, 300, 1, 'кВт'))
		self.assertEqual(self.boiler.get_stage_1_power(), 30)
		self.assertEqual(self.boiler.get_stage_2_power(), 30)
		self.assertEqual(self.boiler.get_analog_power(), 30)

	def test_max_power_counts_only_mapped_stages(self):
		for mappings in product((False, True), repeat=3):
			with self.subTest(mappings=mappings):
				for channel, mapped in zip(self.channels.values(), mappings):
					channel.is_mapped.return_value = mapped
				self.assertEqual(self.boiler.get_max_power(), 30 * sum(mappings))


if __name__ == '__main__':
	unittest.main()
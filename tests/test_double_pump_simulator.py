import unittest
from unittest.mock import Mock, patch

# Import in application order to avoid the mainThread/message import cycle.
import mainThread  # noqa: F401
from presets.preset import get_presetFilesList, get_presets_list, validate_program_presets
from programs.double_pump import DoublePump
from programs.factory import createProgram
from simulator.sensorReport import reportSensorValue
from simulator.simulator import simulatorType
from smartnet.constants import ProgramType, ProgramParameterId, RemoteControlFunction, RequestFlag
from smartnet.units import SENSOR_OPEN_VALUE, SENSOR_SHORT_VALUE


class DoublePumpSimulatorTests(unittest.TestCase):
	def create_model(self, preset_name):
		presets, controllers = get_presets_list(preset_name)
		validate_program_presets(presets)
		# Initial output reads normally require a connected controller.
		with patch('programs.program.Program.read_output', return_value=0):
			program = createProgram(presets[0])
		self.addCleanup(program.clear)
		return program, simulatorType[ProgramType.DOUBLE_PUMP](program, None), controllers

	def test_presets_are_discovered_and_preserve_firmware_indexes(self):
		for name, mapped_ids in (
			('double_pump_discrete', [0, 1, 4]),
			('double_pump_analog', [2, 3, 4]),
		):
			with self.subTest(preset=name):
				self.assertIn(name, get_presetFilesList())
				program, _, controllers = self.create_model(name)
				self.assertIsInstance(program, DoublePump)
				self.assertEqual(program.get_type(), ProgramType.DOUBLE_PUMP)
				self.assertEqual([c.get_id() for c in program.get_inputs().values()], list(range(4)))
				self.assertEqual([c.get_id() for c in program.get_outputs().values()], list(range(5)))
				self.assertEqual([c.get_id() for c in program.get_outputs().values() if c.is_mapped()], mapped_ids)
				for channel in program.get_inputs().values():
					self.assertTrue(channel.isOpen())
					self.assertEqual(channel.get_value(), 0)
					self.assertEqual(channel.getUnits(), '%' if channel.get_id() == 0 else '')
					self.assertEqual(channel.get_mapping().get_channel_id(), channel.get_id())
				for channel in (*program.get_inputs().values(), *program.get_outputs().values()):
					if channel.is_mapped():
						self.assertEqual(channel.get_mapping().get_host_id(), controllers[0].get_id())
						self.assertLess(channel.get_mapping().get_channel_id(), 6)

	def test_each_pump_and_both_pumps_produce_flow_then_stop(self):
		for name, keys in (
			('double_pump_discrete', ('discrete_pump_1', 'discrete_pump_2')),
			('double_pump_analog', ('analog_pump_1', 'analog_pump_2')),
		):
			program, simulator, _ = self.create_model(name)
			flow = program.get_input_channel('flow')
			for first, second in ((0, 0), (1, 0), (0, 127), (254, 254), (0, 0)):
				with self.subTest(preset=name, first=first, second=second):
					program.set_output_value(keys[0], first)
					program.set_output_value(keys[1], second)
					simulator.run()
					self.assertEqual(flow.isShort(), bool(first or second))
					self.assertEqual(flow.isOpen(), not bool(first or second))
					self.assertEqual(program.get_output_channel(keys[0]).get_value(), first)
					self.assertEqual(program.get_output_channel(keys[1]).get_value(), second)

	def test_unknown_unmapped_and_alarm_outputs_do_not_produce_flow(self):
		program, simulator, _ = self.create_model('double_pump_discrete')
		for key in ('discrete_pump_1', 'discrete_pump_2'):
			self.enterContext(patch.object(program.get_output_channel(key), 'get_value', return_value=None))
		for key in ('analog_pump_1', 'analog_pump_2', 'alarm'):
			program.set_output_value(key, 254)
		simulator.run()
		self.assertTrue(program.get_input_channel('flow').isOpen())

	def test_empty_mappings_do_not_produce_flow(self):
		with patch('programs.program.Program.read_output'):
			program = DoublePump(None)
		self.addCleanup(program.clear)
		simulator = simulatorType[ProgramType.DOUBLE_PUMP](program, None)
		for channel in program.get_outputs().values():
			channel.set_value(254)
		simulator.run()
		self.assertTrue(program.get_input_channel('flow').isOpen())

	def test_manual_flow_overrides_auto_in_both_directions(self):
		program, simulator, _ = self.create_model('double_pump_discrete')
		flow = program.get_input_channel('flow')
		flow.set_manual(True)
		flow.set_value('open', manual=True)
		program.set_output_value('discrete_pump_1', 254)
		simulator.run()
		self.assertTrue(flow.isOpen())
		flow.set_manual(False)
		simulator.run()
		self.assertTrue(flow.isShort())
		flow.set_manual(True)
		program.set_output_value('discrete_pump_1', 0)
		simulator.run()
		self.assertTrue(flow.isShort())
		flow.set_manual(False)
		simulator.run()
		self.assertTrue(flow.isOpen())

	def test_control_and_fault_inputs_are_not_changed(self):
		program, simulator, _ = self.create_model('double_pump_analog')
		program.get_input_channel('control').set_value(50)
		for key in ('pump_1_error', 'pump_2_error'):
			program.get_input_channel(key).set_value('short')
		simulator.run()
		self.assertEqual(program.get_input_channel('control').get_value(), 50)
		for key in ('pump_1_error', 'pump_2_error'):
			self.assertTrue(program.get_input_channel(key).isShort())

	def test_controller_output_response_updates_flow(self):
		program, simulator, _ = self.create_model('double_pump_analog')
		message = Mock()
		message.getProgramId.return_value = program.get_id()
		message.get_program_type.return_value = ProgramType.REMOTE_CONTROL
		message.getFunctionId.return_value = RemoteControlFunction.GET_PARAMETER_VALUE
		message.getRequestFlag.return_value = RequestFlag.RESPONSE
		message.get_data.return_value = [ProgramType.PROGRAM, ProgramParameterId.OUTPUT, 3, 64]
		program.on_can_message_received(message)
		simulator.run()
		self.assertTrue(program.get_input_channel('flow').isShort())

	def test_flow_report_uses_discrete_sensor_values(self):
		program, simulator, _ = self.create_model('double_pump_discrete')
		flow = program.get_input_channel('flow')
		with patch('simulator.sensorReport.sm.Message') as message:
			for output, expected in ((0, SENSOR_OPEN_VALUE), (254, SENSOR_SHORT_VALUE)):
				program.set_output_value('discrete_pump_1', output)
				simulator.run()
				self.assertTrue(reportSensorValue(flow))
				mapping = flow.get_mapping()
				self.assertEqual(message.call_args.args[4], [
					mapping.get_raw(0), mapping.get_raw(1),
					(expected >> 8) & 0xFF, expected & 0xFF,
				])


if __name__ == '__main__':
	unittest.main()
"""Alarm program inputs are controlled by scenarios, not by the simulator."""

import unittest
from unittest.mock import Mock, patch

# Import in application order to avoid the existing mainThread/message import cycle.
import mainThread  # noqa: F401
from presets.list.alarm import get_presets_list
from programs.alarm import Alarm
from programs.factory import createProgram, programCreator
from simulator.sensorReport import reportSensorValue
from simulator.simulator import simulatorType
from smartnet.constants import ProgramType
from smartnet.units import SENSOR_OPEN_VALUE, SENSOR_SHORT_VALUE


class AlarmSimulatorTests(unittest.TestCase):
	def setUp(self):
		self.presets, self.controllers = get_presets_list()
		self.program = createProgram(self.presets[0])
		self.addCleanup(self.program.clear)
		self.simulator = simulatorType[ProgramType.ALARM](self.program, None)

	def test_factory_and_all_nine_inputs_match_firmware_indexes(self):
		self.assertIs(programCreator[ProgramType.ALARM], Alarm)
		self.assertIsInstance(self.program, Alarm)
		self.assertEqual(self.program.get_type(), ProgramType.ALARM)
		self.assertEqual(len(self.program.get_inputs()), 9)
		for index in range(8):
			with self.subTest(index=index):
				channel = self.program.get_alarm_input(index)
				self.assertEqual(channel.get_id(), index)
				self.assertTrue(channel.isOpen())
				self.assertTrue(channel.is_mapped())
		reset = self.program.get_reset_input()
		self.assertEqual(reset.get_id(), 8)
		self.assertTrue(reset.isOpen())
		self.assertTrue(reset.is_mapped())

	def test_preset_uses_only_existing_controller_inputs(self):
		self.assertEqual(len(self.controllers), 2)
		self.assertEqual(len(self.presets[0].get_inputs()), 9)
		for index, mapping in enumerate(self.presets[0].get_inputs()):
			controller = self.controllers[index // 6]
			self.assertEqual(mapping.get_host_id(), controller.get_id())
			self.assertEqual(mapping.get_channel_id(), index % 6)
			self.assertLess(mapping.get_channel_id(), 6)

	def test_simulator_never_overwrites_scenario_values(self):
		first = self.program.get_alarm_input(0)
		analog = self.program.get_alarm_input(1)
		reset = self.program.get_reset_input()
		first.set_value('short', True)
		analog.set_value(12.5, True)
		reset.set_value('short', True)
		self.simulator.run()
		self.assertTrue(first.isShort())
		self.assertEqual(analog.get_value(), 12.5)
		self.assertFalse(analog.isOpen())
		self.assertTrue(reset.isShort())
		self.assertTrue(self.program.get_alarm_input(2).isOpen())

	def test_initial_open_state_is_visible_when_gui_is_attached(self):
		channel = self.program.get_reset_input()
		gui = Mock()
		channel.setGui(gui)
		gui._openCheckbox.SetValue.assert_called_with(True)
		gui._slider.Enable.assert_called_with(False)
		gui._spinner.Enable.assert_called_with(False)

	def test_sensor_report_sends_open_short_and_analog_values(self):
		with patch('simulator.sensorReport.sm.Message') as message:
			for channel, value, expected in (
				(self.program.get_alarm_input(0), 'open', SENSOR_OPEN_VALUE),
				(self.program.get_reset_input(), 'short', SENSOR_SHORT_VALUE),
				(self.program.get_alarm_input(1), 12.5, 125),
			):
				with self.subTest(value=value):
					channel.set_value(value, True)
					self.assertTrue(reportSensorValue(channel))
					mapping = channel.get_mapping()
					self.assertEqual(message.call_args.args[4], [
						mapping.get_raw(0), mapping.get_raw(1),
						(expected >> 8) & 0xFF, expected & 0xFF,
					])
					message.return_value.send.assert_called_with(bus=None)


if __name__ == '__main__':
	unittest.main()
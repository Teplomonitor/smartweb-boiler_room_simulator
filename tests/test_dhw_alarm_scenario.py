"""Scenario 3.4.6 checks without GUI, CAN or an external controller."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc
from tests.alarm_scenario_helpers import Sensor, load_alarm_scenario


Scenario = load_alarm_scenario('scenario/list/dhw/scenario_dhw_3_4_6.py')


class TestDhwAlarmScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = Scenario()
		self.scenario.RELAY_OFF = 0
		self.scenario.RELAY_ON = 255
		self.scenario.ALARM_TIMEOUT = 0
		self.pressure, self.temperature = Sensor(3), Sensor(40)
		self.values = {}
		self.initial = {}
		self.fault = None
		self.had_alarm = False
		self.phases = []
		dhw, filling = Mock(), Mock()
		dhw.get_id.return_value = 101
		filling.get_id.return_value = 103
		dhw.get_temperature.return_value = self.temperature
		filling.getPressure.return_value = self.pressure
		self.supply, self.circulation, self.alarm = Mock(), Mock(), Mock()
		self.supply.get_value.side_effect = lambda: self.pump_value('supply')
		self.circulation.get_value.side_effect = lambda: self.pump_value('circulation')
		self.alarm.get_value.side_effect = self.alarm_value
		dhw.get_supply_pump_state.return_value = self.supply
		dhw.get_circulation_pump_state.return_value = self.circulation
		filling.get_output_channel.return_value = self.alarm
		self.scenario._programList = {'dhw': dhw, 'filling_loop': filling}
		self.scenario._read_parameter = Mock(side_effect=self.read_parameter)
		self.scenario._write_parameter = Mock(side_effect=self.write_parameter)
		self.scenario.wait_event = Mock(side_effect=lambda predicate, timeout: predicate())
		self.scenario.wait_state_permanence = Mock(side_effect=self.hold_state)
		self.scenario.simple_wait = Mock()

	def read_parameter(self, program, program_type, parameter_id):
		if self.fault == 'read_failure':
			return None
		key = (program.get_id(), program_type, parameter_id)
		self.values.setdefault(key, 10)
		self.initial.setdefault(key, self.values[key])
		return self.values[key]

	def write_parameter(self, program, program_type, parameter_id, value):
		key = (program.get_id(), program_type, parameter_id)
		self.values[key] = value
		return self.fault != 'write_failure'

	def alarm_value(self):
		if self.fault == 'unknown_alarm':
			return None
		if self.pressure.value == Scenario.PRESSURE_LOW:
			self.had_alarm = True
			return 0 if self.fault == 'no_alarm' else 255
		return 255 if self.fault == 'alarm_stuck' and self.had_alarm else 0

	def pump_value(self, name):
		if self.fault == f'unknown_{name}':
			return None
		if self.fault == f'{name}_never_runs':
			return 0
		if self.pressure.value == Scenario.PRESSURE_LOW:
			return 255 if self.fault == f'{name}_ignores_alarm' else 0
		return 0 if self.fault == f'{name}_no_restart' and self.had_alarm else 255

	def hold_state(self, predicate, duration, timeout):
		self.phases.append(self.pressure.value)
		return all(predicate() for _ in range(3))

	def assert_clean(self):
		self.assertEqual(self.values, self.initial)
		self.assertEqual([self.pressure.value, self.temperature.value], [3, 40])
		self.assertFalse(self.pressure.manual)
		self.assertFalse(self.temperature.manual)

	def test_full_cycle_and_cleanup(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.phases, [3, 0, 3])
		self.assert_clean()
		dhw = self.scenario._programList['dhw']
		for parameter_id, value in (
			(snc.DhwParameterId.WORK_MODE, self.scenario.MODE_COMFORT),
			(snc.DhwParameterId.TEMPERATURE_COMFORT, self.scenario.COMFORT_TEMPERATURE),
			(snc.DhwParameterId.CIRCULATION_MODE, self.scenario.CIRCULATION_ON),
			(snc.DhwParameterId.DHW_RELIEF, self.scenario.PUMP_RELIEF_OFF),
		):
			self.scenario._write_parameter.assert_any_call(dhw, snc.ProgramType.DHW, parameter_id, value)
		self.scenario._write_parameter.assert_any_call(
			dhw, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.ALARM_PROGRAM_ID, 103,
		)

	def test_each_pump_must_follow_all_three_phases(self):
		for pump in ('supply', 'circulation'):
			for fault in ('never_runs', 'ignores_alarm', 'no_restart'):
				with self.subTest(pump=pump, fault=fault):
					self.setUp()
					self.fault = f'{pump}_{fault}'
					self.scenario.run()
					self.assertEqual(self.scenario._status, 'FAIL')
					self.assert_clean()

	def test_alarm_and_io_failures_restore_state(self):
		for fault in ('no_alarm', 'alarm_stuck', 'unknown_alarm', 'unknown_supply',
			'unknown_circulation', 'read_failure', 'write_failure'):
			with self.subTest(fault=fault):
				self.setUp()
				self.fault = fault
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_clean()

	def test_existing_manual_modes_are_preserved(self):
		self.pressure.manual = self.temperature.manual = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertTrue(self.pressure.manual)
		self.assertTrue(self.temperature.manual)
		self.assertEqual([self.pressure.value, self.temperature.value], [3, 40])

	def test_cancellation_during_alarm_restores_state(self):
		def interrupt(predicate, timeout):
			self.alarm_value()
			raise RuntimeError('stopped')
		self.scenario.wait_event.side_effect = interrupt
		with self.assertRaisesRegex(RuntimeError, 'stopped'):
			self.scenario.run()
		self.assertTrue(self.had_alarm)
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_clean()

	def test_restore_failure_does_not_skip_remaining_cleanup(self):
		def write(program, program_type, parameter_id, value):
			key = (program.get_id(), program_type, parameter_id)
			self.values[key] = value
			return value != self.initial[key]
		self.scenario._write_parameter.side_effect = write
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_clean()

	def test_invalid_channels_abort_before_writes(self):
		for channel in ('pressure', 'temperature', 'supply', 'circulation', 'alarm'):
			with self.subTest(channel=channel):
				self.setUp()
				item = getattr(self, channel)
				if isinstance(item, Sensor):
					item.mapped = False
				else:
					item.is_mapped.return_value = False
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.scenario._write_parameter.assert_not_called()
				self.assert_clean()

	def test_unknown_alarm_is_neither_on_nor_off(self):
		self.fault = 'unknown_alarm'
		self.assertFalse(self.scenario.filling_alarm_is_on())
		self.assertFalse(self.scenario.filling_alarm_is_off())


class TestDhwAlarmPreset(unittest.TestCase):
	def test_existing_preset_has_required_programs_and_two_pumps(self):
		root = Path(__file__).resolve().parents[1]
		remote = ModuleType('smartnet.remoteControl')
		remote.RemoteControlParameter = lambda *args: args
		mapping = ModuleType('smartnet.channelMapping')
		mapping.ChannelMapping = lambda *args: args
		with patch.dict(sys.modules, {'smartnet.remoteControl': remote, 'smartnet.channelMapping': mapping}):
			def load(name, path):
				spec = importlib.util.spec_from_file_location(name, root / path)
				module = importlib.util.module_from_spec(spec)
				spec.loader.exec_module(module)
				return module
			settings = load('dhw_settings_under_test', 'presets/settings.py')
			with patch.dict(sys.modules, {'presets.settings': settings}):
				preset = load('dhw_preset_under_test', 'presets/list/dhw.py')
				programs, _ = preset.get_presets_list()
		self.assertTrue(set(Scenario().get_required_programs().values()).issubset(
			{program.get_type() for program in programs},
		))
		self.assertIn((snc.ProgramType.CONSUMER, snc.ConsumerParameterId.ALARM_PROGRAM_ID,
			preset.programId['FILLING_LOOP']), preset.programSettings['DHW'].get())
		self.assertEqual(len(preset.programOutputs['DHW']), 2)
		self.assertEqual(len(set(preset.programOutputs['DHW'])), 2)


if __name__ == '__main__':
	unittest.main()
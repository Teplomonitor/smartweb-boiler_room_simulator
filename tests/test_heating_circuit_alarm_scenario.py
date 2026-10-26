"""Control-flow and cleanup checks for scenario 3.3.11, without hardware."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
	spec = importlib.util.spec_from_file_location(name, ROOT / path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def load_scenario():
	parent = ModuleType('scenario.scenario')
	parent.Scenario = object
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	with patch.dict(sys.modules, {
		'scenario.scenario': parent, 'smartnet.remoteControl': remote, 'consoleLog': console,
	}):
		base = load_module('alarm_base_under_test', 'scenario/base/filling_loop_alarm.py')
		with patch.dict(sys.modules, {'scenario.base.filling_loop_alarm': base}):
			return load_module(
				'circuit_alarm_under_test',
				'scenario/list/heating_circuit/scenario_heating_circuit_3_3_11.py',
			).Scenario


Scenario = load_scenario()


class Sensor:
	def __init__(self, value):
		self.value = value
		self.manual = False
		self.mapped = True

	def get_value(self):
		return self.value

	def set_value(self, value, manual=False):
		self.value = value

	def is_mapped(self):
		return self.mapped

	def isManual(self):
		return self.manual

	def set_manual(self, manual):
		self.manual = manual

	def isShort(self):
		return False

	def isOpen(self):
		return False


class TestHeatingCircuitAlarmScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = Scenario()
		self.scenario.RELAY_OFF = 0
		self.scenario.RELAY_ON = 255
		self.scenario.ALARM_TIMEOUT = 0  # Never block on deliberately stuck mocks.
		self.pressure, self.flow, self.boiler_sensor = [Sensor(value) for value in (3, 25, 45)]
		self.sensors = [self.pressure, self.flow, self.boiler_sensor]
		self.values = {}
		self.initial = {}
		self.fault = None
		self.had_alarm = False
		self.phases = []
		circuit, boiler, filling = Mock(), Mock(), Mock()
		for identifier, program in enumerate((circuit, boiler, filling), 101):
			program.get_id.return_value = identifier
		circuit.get_input_channel.return_value = self.flow
		boiler.get_input_channel.return_value = self.boiler_sensor
		filling.getPressure.return_value = self.pressure
		self.pump, self.alarm = Mock(), Mock()
		self.pump.get_value.side_effect = self.pump_value
		self.alarm.get_value.side_effect = self.alarm_value
		circuit.get_output_channel.return_value = self.pump
		filling.get_output_channel.return_value = self.alarm
		self.scenario._programList = {'heating_circuit': circuit, 'boiler': boiler, 'filling_loop': filling}
		self.scenario._read_parameter = Mock(side_effect=self.read_parameter)
		self.scenario._write_parameter = Mock(side_effect=self.write_parameter)
		self.scenario.wait_event = Mock(side_effect=lambda predicate, timeout: predicate())
		self.scenario.wait_state_permanence = Mock(side_effect=self.hold_state)
		self.scenario.simple_wait = Mock()

	def key(self, program, program_type, parameter_id):
		return program.get_id(), program_type, parameter_id

	def read_parameter(self, program, program_type, parameter_id):
		if self.fault == 'read_failure':
			return None
		key = self.key(program, program_type, parameter_id)
		self.values.setdefault(key, 10)
		self.initial.setdefault(key, self.values[key])
		return self.values[key]

	def write_parameter(self, program, program_type, parameter_id, value):
		key = self.key(program, program_type, parameter_id)
		self.values[key] = value
		return self.fault != 'write_failure'

	def alarm_value(self):
		if self.fault == 'unknown_alarm':
			return None
		if self.pressure.value == Scenario.PRESSURE_LOW:
			self.had_alarm = True
			return 0 if self.fault == 'no_alarm' else 255
		return 255 if self.fault == 'alarm_stuck' and self.had_alarm else 0

	def pump_value(self):
		if self.fault == 'unknown_pump':
			return None
		if self.fault == 'never_runs':
			return 0
		if self.pressure.value == Scenario.PRESSURE_LOW:
			return 255 if self.fault == 'ignores_alarm' else 0
		return 0 if self.fault == 'no_restart' and self.had_alarm else 255

	def hold_state(self, predicate, duration, timeout):
		self.phases.append(self.pressure.value)
		return all(predicate() for _ in range(3))

	def assert_clean(self):
		self.assertEqual(self.values, self.initial)
		self.assertEqual([sensor.value for sensor in self.sensors], [3, 25, 45])
		self.assertEqual([sensor.manual for sensor in self.sensors], [False, False, False])

	def test_complete_cycle(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.phases, [3, 0, 3])
		self.assert_clean()
		self.assertGreaterEqual(self.scenario.STATE_TIMEOUT, 120)

	def test_faults_fail_and_restore(self):
		for fault in ('never_runs', 'unknown_pump', 'unknown_alarm', 'no_alarm', 'ignores_alarm',
			'no_restart', 'alarm_stuck', 'read_failure', 'write_failure'):
			with self.subTest(fault=fault):
				self.setUp()
				self.fault = fault
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_clean()

	def test_original_manual_mode_is_preserved(self):
		self.flow.manual = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertTrue(self.flow.manual)
		self.assertEqual(self.flow.value, 25)

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

	def test_cleanup_does_not_use_interruptible_wait(self):
		self.scenario._pressure = self.pressure
		self.scenario._alarm = self.alarm
		self.scenario.ALARM_TIMEOUT = 60
		self.alarm.get_value.side_effect = [255, 0]
		self.scenario._clear_alarm()
		self.scenario.simple_wait.assert_called_once_with(self.scenario.CLEANUP_POLL_INTERVAL)
		self.scenario.wait_event.assert_not_called()

	def test_restore_failure_does_not_skip_sensors(self):
		def write(program, program_type, parameter_id, value):
			key = self.key(program, program_type, parameter_id)
			self.values[key] = value
			return value != self.initial[key]
		self.scenario._write_parameter.side_effect = write
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_clean()

	def test_invalid_inputs_abort_before_changes(self):
		for invalid in ('unmapped', 'missing_value', 'unsafe_pressure', 'unmapped_pump'):
			with self.subTest(invalid=invalid):
				self.setUp()
				if invalid == 'unmapped':
					self.pressure.mapped = False
				elif invalid == 'missing_value':
					self.flow.value = None
				elif invalid == 'unsafe_pressure':
					self.pressure.value = 0
				else:
					self.pump.is_mapped.return_value = False
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.scenario._write_parameter.assert_not_called()
				self.assertFalse(any(sensor.manual for sensor in self.sensors))


class TestHeatingCircuitAlarmPreset(unittest.TestCase):
	def test_programs_mappings_and_alarm_link(self):
		remote = ModuleType('smartnet.remoteControl')
		remote.RemoteControlParameter = lambda *args: args
		mapping = ModuleType('smartnet.channelMapping')
		mapping.ChannelMapping = lambda *args: args
		with patch.dict(sys.modules, {'smartnet.remoteControl': remote, 'smartnet.channelMapping': mapping}):
			settings = load_module('settings_alarm_under_test', 'presets/settings.py')
			with patch.dict(sys.modules, {'presets.settings': settings}):
				preset = load_module('preset_alarm_under_test', 'presets/list/heating_circuit_3_3_11.py')
				programs, controllers = preset.get_presets_list()
				circuit_settings = programs[0].getSettings()
				parameters = circuit_settings.get()
				legacy = settings.HeatingCircuitSettings(source=102, heatingSlope=0.8).get()
		self.assertEqual({program.get_type() for program in programs}, set(Scenario().get_required_programs().values()))
		self.assertEqual(len({program.get_id() for program in programs}), len(programs))
		self.assertIn((snc.ProgramType.CONSUMER, snc.ConsumerParameterId.ALARM_PROGRAM_ID, preset.FILLING_LOOP_ID), parameters)
		self.assertEqual(circuit_settings.getSourceList(), [preset.BOILER_ID])
		self.assertFalse(any(parameter[1] == snc.ConsumerParameterId.ALARM_PROGRAM_ID
			for parameter in legacy if parameter[0] == snc.ProgramType.CONSUMER))
		for getter in ('get_inputs', 'get_outputs'):
			channels = [channel for program in programs for channel in getattr(program, getter)() if channel is not None]
			self.assertEqual(len(channels), len(set(channels)))
			self.assertTrue(all(channel[2] in {host.get_id() for host in controllers} for channel in channels))
		self.assertIsNotNone(programs[0].get_outputs()[3])
		self.assertIsNotNone(programs[2].get_outputs()[1])


if __name__ == '__main__':
	unittest.main()
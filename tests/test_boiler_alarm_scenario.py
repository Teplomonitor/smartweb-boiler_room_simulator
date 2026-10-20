"""Scenario 3.5.6 control-flow checks without CAN, GUI or a controller."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc


def load_scenario():
	parent = ModuleType('scenario.scenario')
	parent.Scenario = object
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	smartnet = ModuleType('smartnet')
	smartnet.constants = snc
	smartnet.remoteControl = remote
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	path = Path(__file__).resolve().parents[1] / 'scenario/list/boiler/scenario_boiler_3_5_6.py'
	spec = importlib.util.spec_from_file_location('boiler_alarm_under_test', path)
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {
		'scenario.scenario': parent,
		'smartnet': smartnet,
		'smartnet.constants': snc,
		'smartnet.remoteControl': remote,
		'consoleLog': console,
	}):
		spec.loader.exec_module(module)
	return module.Scenario


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


class TestBoilerAlarmScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = Scenario()
		self.scenario.RELAY_OFF = 0
		self.scenario.RELAY_ON = 255
		self.scenario._manualSensorsList = []
		self.pressure, self.boiler_temperature, self.dhw_temperature = [Sensor(v) for v in (3, 30, 40)]
		self.sensors = [self.pressure, self.boiler_temperature, self.dhw_temperature]
		self.values = {}
		self.initial_values = {}
		self.fault = None
		self.had_alarm = False
		self.phases = []
		boiler, dhw, filling_loop = Mock(), Mock(), Mock()
		for identifier, program in enumerate((boiler, dhw, filling_loop), 101):
			program.get_id.return_value = identifier
		boiler.get_input_channel.return_value = self.boiler_temperature
		dhw.get_temperature.return_value = self.dhw_temperature
		filling_loop.getPressure.return_value = self.pressure
		self.alarm = Mock()
		self.alarm.get_value.side_effect = self.alarm_value
		filling_loop.get_output_channel.return_value = self.alarm
		self.stage_1, self.stage_2, self.pump = Mock(), Mock(), Mock()
		self.stage_1.get_value.side_effect = self.heating_value
		self.stage_2.get_value.return_value = 0
		self.pump.get_value.side_effect = self.heating_value
		boiler.get_stage_1.return_value = self.stage_1
		boiler.get_output_channel.return_value = self.stage_2
		boiler.get_pump.return_value = self.pump
		self.scenario._programList = {'boiler': boiler, 'dhw': dhw, 'filling_loop': filling_loop}
		self.scenario._read_parameter = Mock(side_effect=self.read_parameter)
		self.scenario._write_parameter = Mock(side_effect=self.write_parameter)
		self.scenario.set_sensor_value = self.set_sensor_value
		self.scenario.wait_event = Mock(side_effect=lambda predicate, timeout: predicate())
		self.scenario.wait_state_permanence = Mock(side_effect=self.hold_state)

	def set_sensor_value(self, sensor, value):
		sensor.set_manual(True)
		sensor.set_value(value, True)
		if sensor not in self.scenario._manualSensorsList:
			self.scenario._manualSensorsList.append(sensor)

	def alarm_value(self):
		if self.pressure.value == Scenario.PRESSURE_LOW:
			self.had_alarm = True
			return 255
		return 255 if self.fault == 'alarm_stuck' and self.had_alarm else 0

	def heating_value(self):
		if self.fault == 'never_heats':
			return 0
		if self.fault == 'unknown_output':
			return None
		if self.pressure.value == Scenario.PRESSURE_LOW:
			return 255 if self.fault == 'ignores_alarm' else 0
		return 0 if self.fault == 'no_restart' and self.had_alarm else 255

	def read_parameter(self, parameter):
		if parameter[:2] == (snc.ProgramType.CONSUMER, snc.ConsumerParameterId.REQUIRED_TEMPERATURE):
			return None if self.fault == 'lost_request' and self.had_alarm else 60
		if self.fault == 'read_failure':
			return None
		self.values.setdefault(parameter, 10)
		self.initial_values.setdefault(parameter, self.values[parameter])
		return self.values[parameter]

	def write_parameter(self, parameter, value):
		self.values[parameter] = value
		return self.fault != 'write_failure'

	def hold_state(self, predicate, duration, timeout):
		self.phases.append(self.pressure.value)
		return all(predicate() for _ in range(3))

	def assert_clean(self):
		self.assertEqual(self.values, self.initial_values)
		self.assertEqual([sensor.value for sensor in self.sensors], [3, 30, 40])
		self.assertFalse(any(sensor.manual for sensor in self.sensors))
		self.assertEqual(self.scenario._manualSensorsList, [])

	def test_complete_cycle_and_cleanup(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.phases, [3, 0, 3])
		self.assert_clean()

	def test_existing_manual_mode_is_preserved(self):
		self.boiler_temperature.manual = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual([sensor.manual for sensor in self.sensors], [False, True, False])
		self.assertEqual(self.boiler_temperature.value, 30)
		self.assertEqual(self.scenario._manualSensorsList, [])

	def test_faults_fail_and_restore_inputs(self):
		for fault in ('never_heats', 'unknown_output', 'ignores_alarm', 'no_restart', 'alarm_stuck', 'lost_request', 'write_failure', 'read_failure'):
			with self.subTest(fault=fault):
				self.setUp()
				self.fault = fault
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_clean()

	def test_second_stage_must_switch_off(self):
		self.stage_2.get_value.return_value = 255
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_clean()

	def test_unmapped_sensor_fails_before_writing(self):
		self.pressure.mapped = False
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.scenario._write_parameter.assert_not_called()

	def test_interruption_still_restores_inputs(self):
		self.scenario.wait_state_permanence.side_effect = RuntimeError('stopped')
		with self.assertRaisesRegex(RuntimeError, 'stopped'):
			self.scenario.run()
		self.assert_clean()

	def test_failed_restoration_marks_failure(self):
		def write(parameter, value):
			self.values[parameter] = value
			return value != self.initial_values[parameter]
		self.scenario._write_parameter.side_effect = write
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_clean()

	def test_parameter_io_uses_supported_remote_api(self):
		parameter = (snc.ProgramType.DHW, snc.DhwParameterId.WORK_MODE, 101)
		remote = Scenario._read_parameter.__globals__['sr'].RemoteControlParameter
		remote.reset_mock()
		remote.return_value.read.return_value = False
		self.assertIsNone(Scenario._read_parameter(self.scenario, parameter))
		remote.return_value.write.return_value = True
		self.assertTrue(Scenario._write_parameter(self.scenario, parameter, 0))
		remote.assert_called_with(
			programType=parameter[0], parameterId=parameter[1], programId=101, parameterValue=0,
		)


class TestBoilerAlarmPreset(unittest.TestCase):
	def test_alarm_targets_boiler_and_consumer_keeps_its_source(self):
		root = Path(__file__).resolve().parents[1]
		remote = ModuleType('smartnet.remoteControl')
		remote.RemoteControlParameter = lambda *args: args
		mapping = ModuleType('smartnet.channelMapping')
		mapping.ChannelMapping = lambda *args: args
		settings_spec = importlib.util.spec_from_file_location('preset_settings_under_test', root / 'presets/settings.py')
		settings = importlib.util.module_from_spec(settings_spec)
		preset_spec = importlib.util.spec_from_file_location('boiler_alarm_preset_under_test', root / 'presets/list/boiler_3_5_6.py')
		preset = importlib.util.module_from_spec(preset_spec)
		with patch.dict(sys.modules, {
			'smartnet.remoteControl': remote,
			'smartnet.channelMapping': mapping,
			'presets.settings': settings,
		}):
			settings_spec.loader.exec_module(settings)
			preset_spec.loader.exec_module(preset)
			programs, controllers = preset.get_presets_list()
		self.assertEqual({program.get_type() for program in programs}, set(Scenario().get_required_programs().values()))
		self.assertEqual(len(controllers), 2)
		self.assertEqual(preset.programSettings['BOILER'].get(), [(
			snc.ProgramType.TEMPERATURE_SOURCE,
			snc.TemperatureSourceParameterId.ALARM_PROGRAM_ID,
			preset.programId['FILLING_LOOP'],
		)])
		self.assertEqual(preset.programSettings['DHW'].get(), [(
			snc.ProgramType.CONSUMER,
			snc.ConsumerParameterId.GENERATOR_ID,
			preset.programId['BOILER'],
		)])
		outputs = [channel for channels in preset.programOutputs.values() for channel in channels]
		self.assertEqual(len(outputs), len(set(outputs)))
		self.assertEqual(len(preset.programOutputs['BOILER']), 3)


if __name__ == '__main__':
	unittest.main()
"""Scripted controller replies test orchestration, NOT firmware behaviour."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc
from smartnet.channelMapping import ChannelMapping, InputChannel, OutputChannel


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
	spec = importlib.util.spec_from_file_location(name, ROOT / path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


class ScenarioParent:
	RELAY_ON = 255
	RELAY_OFF = 0

	def set_sensor_value(self, sensor, value):
		sensor.set_manual(True)
		if sensor not in self._manualSensorsList:
			self._manualSensorsList.append(sensor)
		sensor.set_value(value, True)


parent = ModuleType('scenario.scenario')
parent.Scenario = ScenarioParent
remote = ModuleType('smartnet.remoteControl')
remote.RemoteControlParameter = Mock()
console = ModuleType('consoleLog')
console.print_log = Mock()
console.print_error = Mock()
with patch.dict(sys.modules, {
	'scenario.scenario': parent, 'smartnet.remoteControl': remote, 'consoleLog': console,
}):
	base = load_module('line_scenario_parent', 'scenario/base/cascade_manager.py')
	with patch.dict(sys.modules, {'scenario.base.cascade_manager': base}):
		line_base = load_module('line_scenario_base', 'scenario/base/heating_circuit_line.py')
	with patch.dict(sys.modules, {'scenario.base.heating_circuit_line': line_base}):
		module = load_module('line_scenario_test', 'scenario/list/heating_circuit/scenario_heating_circuit_3_3_6.py')
		temperature_module = load_module('line_temperature_test', 'scenario/list/heating_circuit/scenario_heating_circuit_3_3_7.py')
	preset = load_module('line_preset_test', 'presets/list/heating_circuit_3_3_6.py')


class LineScenarioHarness(unittest.TestCase):
	SCENARIO_CLASS = module.Scenario

	def setUp(self):
		self.scenario = self.SCENARIO_CLASS()
		self.scenario._manualSensorsList = []
		self.programs, self.controllers = preset.get_presets_list()
		remaining = list(self.programs)
		self.scenario._programList = {}
		self.preset_by_id = {program.get_id(): program for program in self.programs}
		self.sensors = []
		for name, program_type in self.scenario.get_required_programs().items():
			definition = next(program for program in remaining if program.get_type() == program_type)
			remaining.remove(definition)
			program = Mock()
			program.get_id.return_value = definition.get_id()
			inputs = {}
			for index, mapping in enumerate(definition.get_inputs()):
				inputs[index] = InputChannel(mapping, 22)
				if mapping and mapping.is_mapped():
					self.sensors.append(inputs[index])
			input_indexes = {
				'temperature': 0, 'outdoorTemperature': 0,
				'thermostat': 1, 'outsideRequest': 2, 'pumpControl': 3,
			}
			program.get_input_channel.side_effect = lambda key, channels=inputs: channels.setdefault(
				input_indexes[key], InputChannel(),
			)
			outputs = {index: OutputChannel(mapping, 0) for index, mapping in enumerate(definition.get_outputs())}
			pump_index = 3 if program_type == snc.ProgramType.HEATING_CIRCUIT else 0
			program.get_output_channel.side_effect = lambda key, channels=outputs, index=pump_index: channels.setdefault(
				index, OutputChannel(),
			)
			self.scenario._programList[name] = program
		for index, sensor in enumerate(self.sensors):
			sensor.set_manual(bool(index % 2))
		self.original_sensors = [(sensor, sensor.get_value(), sensor.isManual()) for sensor in self.sensors]
		self.settings = self.scenario._settings()
		self.initial = {
			(program.get_id(), program_type, parameter_id, None): value + 1
			for program, program_type, parameter_id, value in self.settings
		}
		self.values = self.initial.copy()
		self.replies = {}
		self.phases = []
		self.writes = []
		self.fault = None
		self.fail_write_number = None
		self.scenario.wait_event = Mock(side_effect=self.observe_requests)
		self.scenario.wait_state_permanence = Mock(side_effect=self.observe_line)

	def parameter(self, programType, parameterId, programId, parameterIndex=None, parameterValue=None):
		key = programId, programType, parameterId, parameterIndex
		parameter = Mock()

		def read():
			value = self.read_value(key)
			parameter.get_value.return_value = value
			return value is not None

		def write():
			self.writes.append((key, parameterValue))
			self.values[key] = parameterValue
			# A lost response may follow a successful controller-side write.
			return len(self.writes) != self.fail_write_number

		parameter.read.side_effect = read
		parameter.write.side_effect = write
		return parameter

	def read_value(self, key):
		program_id, program_type, parameter_id, index = key
		if key in self.replies:
			return self.replies[key]
		if key in self.values:
			return self.values[key]
		definition = self.preset_by_id[program_id]
		if program_type == snc.ProgramType.PROGRAM and parameter_id == snc.ProgramParameterId.SCHEME:
			return snc.ProgramScheme[definition.get_scheme()]
		if program_type == snc.ProgramType.CONSUMER and parameter_id == snc.ConsumerParameterId.GENERATOR_ID:
			return definition.getSettings().getSource()
		if program_type == snc.ProgramType.CASCADE_MANAGER and parameter_id == snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID:
			return definition.getSettings().getSourceList()[index]
		raise AssertionError(f'Unexpected read: {key}')

	def observe_requests(self, predicate, timeout):
		self.assertEqual(timeout, self.scenario.CONSUMER_TIMEOUT)
		active = self.scenario.PHASES[len(self.phases)]
		self.phases.append(active)
		for circuit, enabled in zip(self.scenario._circuits(), active[:2]):
			self.assertEqual(self.values[circuit.get_id(), snc.ProgramType.HEATING_CIRCUIT,
				snc.HeatingCircuitParameterId.PUMP_MODE, None], 2 if enabled else 3)
		self.assertEqual(self.values[preset.DHW_ID, snc.ProgramType.DHW,
			snc.DhwParameterId.WORK_MODE, None], 0 if active[2] else 3)
		# Fixed reference replies: no regulation or CAN timing is emulated here.
		for program_id, request, enabled in zip(
			[*preset.CIRCUIT_IDS, preset.DHW_ID], (40, 50, 55), active,
		):
			self.replies[program_id, snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE, None] = request if enabled else 0
		if self.fault == 'consumer':
			self.replies[preset.CIRCUIT_IDS[0], snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE, None] = 99
		return predicate()

	def observe_line(self, predicate, duration, timeout):
		self.assertGreater(duration, 2 * 20 + 60)
		self.assertEqual(timeout, self.scenario.LINE_TIMEOUT)
		active = self.phases[-1]
		expected = max((request for request, enabled in zip((40, 50, 55), active) if enabled), default=0)
		pump = self.scenario._programList['heating_line'].get_output_channel('pump')
		pump.set_value(255 if any(active) else 0)
		self.replies[preset.HEATING_LINE_ID, snc.ProgramType.CONSUMER,
			snc.ConsumerParameterId.REQUIRED_TEMPERATURE, None] = expected
		self.replies[preset.CASCADE_ID, snc.ProgramType.TEMPERATURE_SOURCE,
			snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE, None] = expected
		if self.fault == 'stuck_on':
			pump.set_value(255)
		elif self.fault == 'stuck_off':
			pump.set_value(0)
		elif self.fault == 'invalid_relay':
			pump.set_value(None)
		elif self.fault in ('line_request', 'missing_read', 'invalid_read'):
			self.replies[preset.HEATING_LINE_ID, snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE, None] = {
				'line_request': 99, 'missing_read': None, 'invalid_read': 'OPEN',
			}[self.fault]
		elif self.fault == 'cascade':
			self.replies[preset.CASCADE_ID, snc.ProgramType.TEMPERATURE_SOURCE,
				snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE, None] = 99
		elif self.fault == 'no_restart' and len(self.phases) == 10:
			pump.set_value(0)
		elif self.fault == 'lost_remaining_request' and len(self.phases) == 4:
			pump.set_value(0)
		return all(predicate() for _ in range(3))

	def run_scenario(self):
		with patch.object(base.sr, 'RemoteControlParameter', side_effect=self.parameter):
			self.scenario.run()

	def assert_restored(self):
		self.assertEqual(self.values, self.initial)
		for sensor, value, manual in self.original_sensors:
			self.assertEqual(sensor.get_value(), value)
			self.assertEqual(sensor.isManual(), manual)
		self.assertEqual(self.scenario._manualSensorsList, [])


class TestHeatingCircuitLineScenario(LineScenarioHarness):
	def test_preset_topology_and_unique_channels(self):
		self.assertEqual(len(self.programs), 8)
		self.assertEqual(self.controllers[0].get_id(), preset.HOST_ID)
		self.assertEqual(len(self.preset_by_id), len(self.programs))
		for channel_type in ('get_inputs', 'get_outputs'):
			channels = [mapping.get_raw() for program in self.programs
				for mapping in getattr(program, channel_type)() if mapping and mapping.is_mapped()]
			self.assertEqual(len(channels), len(set(channels)))
		self.run_scenario()
		self.assertEqual(self.scenario._status, 'OK')

	def test_success_all_phases_and_restoration(self):
		self.run_scenario()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.phases, list(self.scenario.PHASES))
		self.assertTrue(self.scenario.force_preset_load())
		self.assert_restored()

	def test_faults_fail_and_restore(self):
		for fault in ('consumer', 'stuck_on', 'stuck_off', 'invalid_relay', 'line_request',
			'missing_read', 'invalid_read', 'cascade', 'no_restart', 'lost_remaining_request'):
			with self.subTest(fault=fault):
				self.setUp()
				self.fault = fault
				self.run_scenario()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_restored()

	def test_wrong_topology_prevents_writes(self):
		for key, value in (
			((preset.HEATING_LINE_ID, snc.ProgramType.PROGRAM, snc.ProgramParameterId.SCHEME, None), 0),
			((preset.DHW_ID, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID, None), preset.CASCADE_ID),
			((preset.CASCADE_ID, snc.ProgramType.CASCADE_MANAGER, snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID, 1), 0),
		):
			with self.subTest(key=key):
				self.setUp()
				self.replies[key] = value
				self.run_scenario()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assertEqual(self.writes, [])

	def test_missing_pump_prevents_writes(self):
		self.scenario._programList['heating_line'].get_output_channel('pump').set_mapping(None)
		self.run_scenario()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.writes, [])

	def test_invalid_sensor_prevents_writes(self):
		for value in (None, 'OPEN', float('nan')):
			with self.subTest(value=value):
				self.setUp()
				with patch.object(self.sensors[0], 'get_value', return_value=value):
					self.run_scenario()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assertEqual(self.writes, [])

	def test_missing_or_faulty_sensor_prevents_writes(self):
		for fault in ('unmapped', 'short', 'open'):
			with self.subTest(fault=fault):
				self.setUp()
				if fault == 'unmapped':
					self.sensors[0].set_mapping(None)
				else:
					self.sensors[0].set_value(fault, True)
				self.run_scenario()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assertEqual(self.writes, [])

	def test_external_input_prevents_writes(self):
		self.scenario._programList['heating_line'].get_input_channel('pumpControl').set_mapping(
			ChannelMapping(20, 'CHANNEL_SENSOR', preset.HOST_ID),
		)
		self.run_scenario()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.writes, [])

	def test_failed_initial_read_prevents_writes(self):
		self.replies[next(iter(self.initial))] = None
		self.run_scenario()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.writes, [])
		self.assert_restored()

	def test_failed_write_restores_attempted_settings(self):
		self.fail_write_number = 3
		self.run_scenario()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(len(self.writes), 6)
		self.assert_restored()

	def test_stop_restores_all_settings_and_manual_sensors(self):
		self.scenario.wait_state_permanence.side_effect = InterruptedError('stopped')
		with self.assertRaisesRegex(InterruptedError, 'stopped'):
			self.run_scenario()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_restore_failure_keeps_fail_status_and_restores_sensors(self):
		# Settings, three writes per phase, then the first restoration write.
		self.fail_write_number = len(self.settings) + 3 * len(self.scenario.PHASES) + 1
		self.run_scenario()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()


class TestHeatingCircuitLineTemperatureScenario(LineScenarioHarness):
	SCENARIO_CLASS = temperature_module.Scenario
	# Independent scripted references, not a simulation of firmware regulation.
	EXPECTED_TEMPERATURES = (45, 45, 45, 50, 60, 55, 60, 55, 45, 60, 45)
	EXPECTED_REQUESTS = (
		(0, 0), (35, 40), (45, 40), (50, 0), (50, 60), (55, 40),
		(55, 60), (55, 0), (0, 0), (0, 60), (0, 0),
	)

	def observe_requests(self, predicate, timeout):
		self.assertEqual(timeout, self.scenario.CONSUMER_TIMEOUT)
		phase_index = len(self.phases)
		phase = self.scenario.PHASES[phase_index]
		requests, active, expected = phase
		self.phases.append(phase)
		self.assertEqual(expected, self.EXPECTED_TEMPERATURES[phase_index])
		for circuit, request, enabled, reply in zip(
			self.scenario._circuits(), requests, active, self.EXPECTED_REQUESTS[phase_index],
		):
			self.assertEqual(self.values[circuit.get_id(), snc.ProgramType.CIRCUIT,
				snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, None], request)
			self.assertEqual(self.values[circuit.get_id(), snc.ProgramType.HEATING_CIRCUIT,
				snc.HeatingCircuitParameterId.PUMP_MODE, None], 2 if enabled else 3)
			self.replies[circuit.get_id(), snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE, None] = reply
		self.assertEqual(self.values[preset.HEATING_LINE_ID, snc.ProgramType.HEATING_CIRCUIT,
			snc.HeatingCircuitParameterId.PUMP_MODE, None], 2)
		self.assertEqual(self.values[preset.DHW_ID, snc.ProgramType.DHW,
			snc.DhwParameterId.WORK_MODE, None], 3)
		self.replies[preset.DHW_ID, snc.ProgramType.CONSUMER,
			snc.ConsumerParameterId.REQUIRED_TEMPERATURE, None] = 0
		if self.fault in ('consumer', 'unexpected_dhw'):
			program_id = preset.CIRCUIT_IDS[0] if self.fault == 'consumer' else preset.DHW_ID
			self.replies[program_id, snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.REQUIRED_TEMPERATURE, None] = 99
		return predicate()

	def observe_line(self, predicate, duration, timeout):
		self.assertGreater(duration, 2 * 20 + 60)
		self.assertEqual(timeout, self.scenario.LINE_TIMEOUT)
		phase_index = len(self.phases) - 1
		expected = self.EXPECTED_TEMPERATURES[phase_index]
		pump = self.scenario._programList['heating_line'].get_output_channel('pump')
		pump.set_value(255)
		line_key = (preset.HEATING_LINE_ID, snc.ProgramType.CONSUMER,
			snc.ConsumerParameterId.REQUIRED_TEMPERATURE, None)
		cascade_key = (preset.CASCADE_ID, snc.ProgramType.TEMPERATURE_SOURCE,
			snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE, None)
		self.replies[line_key] = expected
		self.replies[cascade_key] = expected
		if self.fault == 'stuck_off':
			pump.set_value(0)
		elif self.fault == 'invalid_relay':
			pump.set_value(None)
		elif self.fault in ('line_request', 'missing_read', 'invalid_read'):
			self.replies[line_key] = {'line_request': 99, 'missing_read': None,
				'invalid_read': 'OPEN'}[self.fault]
		elif self.fault == 'cascade':
			self.replies[cascade_key] = 99
		elif self.fault == 'ignored_downstream' and phase_index == 3:
			self.replies[line_key] = 45
		elif self.fault == 'stale_maximum' and phase_index == 5:
			self.replies[line_key] = 60
		elif self.fault == 'lost_own_setpoint' and phase_index == 8:
			self.replies[line_key] = 0
		elif self.fault == 'no_restart' and phase_index == 9:
			self.replies[line_key] = 45
		return all(predicate() for _ in range(3))

	def test_success_all_reference_points_and_restoration(self):
		self.run_scenario()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.phases, list(self.scenario.PHASES))
		self.assertEqual(self.scenario.get_checklist_id(), '3.3.7')
		self.assertEqual(self.scenario.get_default_preset(), 'heating_circuit_3_3_6')
		self.assert_restored()

	def test_faults_fail_and_restore(self):
		for fault in ('consumer', 'unexpected_dhw', 'stuck_off', 'invalid_relay',
			'line_request', 'missing_read', 'invalid_read', 'cascade',
			'ignored_downstream', 'stale_maximum', 'lost_own_setpoint', 'no_restart'):
			with self.subTest(fault=fault):
				self.setUp()
				self.fault = fault
				self.run_scenario()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_restored()

	def test_failed_phase_write_restores_changed_setpoints(self):
		self.fail_write_number = len(self.settings) + 5
		self.run_scenario()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_stop_restores_changed_setpoints_and_sensors(self):
		self.scenario.wait_state_permanence.side_effect = InterruptedError('stopped')
		with self.assertRaisesRegex(InterruptedError, 'stopped'):
			self.run_scenario()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_restore_failure_keeps_fail_status(self):
		self.fail_write_number = len(self.settings) + 4 * len(self.scenario.PHASES) + 1
		self.run_scenario()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()


if __name__ == '__main__':
	unittest.main()
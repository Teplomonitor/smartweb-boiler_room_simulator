"""Scripted protocol and restoration tests; these do not run the firmware."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc
from tests.test_scenario_steps import Sensor, load_steps


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
	spec = importlib.util.spec_from_file_location(name, ROOT / path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


class Input(Sensor):
	def is_mapped(self):
		return True


class Output:
	def __init__(self):
		self.value = 255
		self.mapped = True

	def get_value(self):
		return self.value

	def is_mapped(self):
		return self.mapped


class ExternalPriorityTests(unittest.TestCase):
	def test_dedicated_presets_match_required_programs(self):
		remote = ModuleType('smartnet.remoteControl')
		remote.RemoteControlParameter = Mock()
		with patch.dict(sys.modules, {'smartnet.remoteControl': remote}):
			for path, types in (
				('presets/list/dhw_external_priority.py', [snc.ProgramType.DHW, snc.ProgramType.BOILER]),
				('presets/list/heating_circuit_external_priority.py',
					[snc.ProgramType.HEATING_CIRCUIT] * 3 +
					[snc.ProgramType.BOILER, snc.ProgramType.OUTDOOR_SENSOR]),
			):
				with self.subTest(path=path):
					programs, controllers = load_module(path, path).get_presets_list()
					self.assertEqual([program.get_type() for program in programs], types)
					self.assertEqual(len({program.get_id() for program in programs}), len(programs))
					self.assertTrue(programs[-1].get_inputs()[0])
					self.assertTrue(controllers)

	def setUp(self):
		self.frames = []
		self.values = {}
		self.errors = Mock()
		parent = ModuleType('scenario.scenario')
		parent.Scenario = type('Parent', (), {'__init__': lambda self, *args: None,
			'RELAY_OFF': 0})
		console = ModuleType('consoleLog')
		console.print_error = self.errors
		console.print_log = Mock()
		message = ModuleType('smartnet.message')
		message.Message = lambda **kwargs: SimpleNamespace(send=lambda: self.frames.append(kwargs))
		remote = ModuleType('smartnet.remoteControl')
		remote.RemoteControlParameter = Mock(side_effect=self.parameter)
		with patch.dict(sys.modules, {'scenario.scenario': parent, 'scenario.steps': load_steps(),
			'consoleLog': console, 'smartnet.message': message, 'smartnet.remoteControl': remote}):
			self.base = load_module('external_priority_test', 'scenario/base/external_priority.py')
		self.scenario = self.base.ExternalPriorityScenario(None, None)
		self.scenario._manualSensorsList = []
		self.scenario._programList = {}
		self.scenario._status = 'IN_PROGRESS'
		self.scenario.set_sensor_value = self.set_sensor
		self.scenario._expect = self.expect
		self.fail_when = None
		self.output = Output()
		self.sensors = []

	def parameter(self, programType, parameterId, programId, parameterIndex=None, parameterValue=None):
		key = (programId, programType, parameterId, parameterIndex)
		def value():
			if key == (programId, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID, None):
				return self.values.get(key, 102)
			if programType == snc.ProgramType.PROGRAM and parameterId == snc.ProgramParameterId.SCHEME:
				return snc.ProgramScheme['CIRCUIT_MIXED'] if programId == 101 else snc.ProgramScheme['CIRCUIT_DIRECT']
			if (programType == snc.ProgramType.POOL and
					parameterId == snc.SwimmingPoolParameterId.CURRENT_REQUIRED_POOL_TEMPERATURE):
				requests = [frame for frame in self.frames
					if frame['functionId'] == snc.ConsumerFunction['GIVE_WAY']]
				return 0 if (self.scenario._active_priority and
					self.scenario._active_priority > self.scenario.LOCAL_PRIORITY and
					requests[-1]['data'][2] == self.scenario._generator_id) else 28
			return self.values.get(key, 1)
		def write():
			self.values[key] = parameterValue
			return True
		return SimpleNamespace(read=lambda: value() is not None, get_value=value, write=write)

	def program(self, program_id, inputs=None, outputs=None):
		inputs = inputs or {}
		outputs = outputs or {}
		return SimpleNamespace(get_id=lambda: program_id,
			get_input_channel=lambda key: inputs[key], get_output_channel=lambda key: outputs[key],
			get_temperature=lambda: inputs['temperature'],
			getDirectFlowTemperature=lambda: inputs['directFlowTemperature'],
			getBackwardFlowTemperature=lambda: inputs['backwardTemperature'],
			getPlateTemperature=lambda: inputs['plateTemperature'],
			getOutdoorTemperature=lambda: inputs['outdoorTemperature'])

	def setup_target(self, target):
		self.scenario.TARGET = target
		if target in ('mixed', 'direct'):
			self.sensors = [Input(15), Input(30)]
			self.scenario._programList = {
				'mixed': self.program(101, outputs={'pump': self.output, 'analogValve': Output()}),
				'direct': self.program(103, outputs={'pump': self.output,
					**{key: SimpleNamespace(is_mapped=lambda: False) for key in
					('analogValve', 'tptValveOpen', 'tptValveClose', 'thermomotor')}}),
				'boiler': self.program(102, inputs={'temperature': self.sensors[1]}),
				'oat': self.program(104, inputs={'outdoorTemperature': self.sensors[0]}),
			}
			self.values[(103, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID, None)] = 102
		elif target == 'snow':
			self.sensors = [Input(20), Input(20), Input(0), Input(5)]
			self.scenario._programList = {
				'consumer': self.program(101, inputs=dict(zip(('directFlowTemperature',
					'backwardTemperature', 'plateTemperature'), self.sensors)),
					outputs={'primaryPump': self.output, 'secondaryPump': self.output}),
				'boiler': self.program(102),
				'oat': self.program(103, inputs={'outdoorTemperature': self.sensors[3]}),
			}
			for key, value in ((snc.SnowMelterParameterId.MINIMUM_OUTDOOR_TEMPERATURE, -10),
					(snc.SnowMelterParameterId.MAXIMUM_OUTDOOR_TEMPERATURE, 15),
					(snc.SnowMelterParameterId.REQUIRED_PLATE_TEMPERATURE, 10),
					(snc.SnowMelterParameterId.PRIMARY_CIRCUIT_PROTECTION_TEMPERATURE, 5),
					(snc.SnowMelterParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE_OF_SECONDARY_CIRCUIT, 40)):
				self.values[(101, snc.ProgramType.SNOWMELT, key, None)] = value
		elif target == 'dhw':
			self.sensors = [Input(20), Input(60)]
			self.scenario._programList = {
				'consumer': self.program(101, inputs={'temperature': self.sensors[0]},
					outputs={'supplyPump': self.output}),
				'boiler': self.program(102, inputs={'temperature': self.sensors[1]}),
			}
		else:
			self.sensors = [Input(20)]
			self.scenario._programList = {
				'consumer': self.program(101, inputs={'temperature': self.sensors[0]},
					outputs={'supplyPump': self.output}), 'boiler': self.program(102),
			}

	def set_sensor(self, sensor, value):
		sensor.set_manual(True)
		sensor.set_value(value, True)
		if sensor not in self.scenario._manualSensorsList:
			self.scenario._manualSensorsList.append(sensor)

	def expect(self, title, condition, timeout=None, hold=0):
		if self.fail_when and self.fail_when in title:
			raise RuntimeError('scripted failure')
		priority = self.scenario._active_priority
		if self.scenario.TARGET != 'pool':
			requests = [frame for frame in self.frames
				if frame['functionId'] == snc.ConsumerFunction['GIVE_WAY']]
			if requests and requests[-1]['data'][2] != self.scenario._generator_id:
				priority = None
			delta = priority - self.scenario.LOCAL_PRIORITY if priority else 0
			threshold = 4 if self.scenario.TARGET == 'mixed' else 1
			self.output.value = 0 if delta >= threshold and not self.scenario._cooling else 255
			if self.scenario.TARGET == 'snow' and self.sensors[1].value < 5:
				self.output.value = 255
			if self.scenario.TARGET == 'mixed' and self.sensors[0].value < 5:
				self.output.value = 255
		if not condition():
			raise RuntimeError(title)

	def assert_clean(self):
		self.assertEqual(self.scenario._active_priority, None)
		self.assertFalse(self.scenario._cooling)
		self.assertEqual(self.scenario._manualSensorsList, [])
		self.assertTrue(all(not sensor.isManual() for sensor in self.sensors))
		self.assertEqual([sensor.get_value() for sensor in self.sensors],
			[15, 30] if self.scenario.TARGET in ('mixed', 'direct') else
			[20, 20, 0, 5] if self.scenario.TARGET == 'snow' else
			[20, 60] if self.scenario.TARGET == 'dhw' else [20])

	def test_frames_and_delta_boundaries(self):
		for target in ('mixed', 'direct'):
			with self.subTest(target=target):
				self.setup_target(target)
				self.scenario._run_external_test('pump')
				self.assertEqual(self.scenario._status, 'OK', self.errors.call_args_list)
				give_way = [frame['data'] for frame in self.frames
					if frame['functionId'] == snc.ConsumerFunction['GIVE_WAY']]
				self.assertEqual(give_way[0][1], 8 if target == 'mixed' else 5)
				self.assertEqual(give_way[-1][1], 9 if target == 'mixed' else 6)
				self.assertEqual(give_way[-1][2], 102)
				self.assertEqual(self.frames[-1]['functionId'], snc.ConsumerFunction['PROCEED'])
				self.assert_clean()
				self.frames.clear()

	def test_dhw_and_snow_pumps(self):
		for target, case in (('dhw', 'pump'), ('snow', 'pump_primary'), ('snow', 'pump')):
			with self.subTest(target=target, case=case):
				self.setup_target(target)
				self.scenario._run_external_test(case)
				self.assertEqual(self.scenario._status, 'OK', self.errors.call_args_list)
				self.assert_clean()
				self.frames.clear()

	def test_both_frost_and_heat_dump_exceptions(self):
		for target in ('snow', 'mixed'):
			with self.subTest(target=target):
				self.setup_target(target)
				self.scenario._run_external_test('exception')
				self.assertEqual(self.scenario._status, 'OK', self.errors.call_args_list)
				self.assert_clean()
				self.assertEqual([frame['data'] for frame in self.frames
					if frame['functionId'] == snc.ConsumerFunction['SET_COOLING']][-1], [102, 0])
				self.frames.clear()

	def test_pool_recovers_and_cleans_up_on_failure(self):
		self.setup_target('pool')
		self.scenario._run_external_test('pool')
		self.assertEqual(self.scenario._status, 'OK')
		self.assert_clean()
		self.fail_when = 'обнуляет'
		self.scenario._run_external_test('pool')
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.frames[-1]['functionId'], snc.ConsumerFunction['PROCEED'])
		self.assert_clean()

	def test_snow_frost_and_cooling_are_cleared_on_failure(self):
		self.setup_target('snow')
		self.fail_when = 'Защита от замерзания'
		self.scenario._run_external_test('exception')
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_clean()
		cooling = [frame['data'] for frame in self.frames
			if frame['functionId'] == snc.ConsumerFunction['SET_COOLING']]
		self.assertEqual(cooling[-1], [102, 0])
		self.assertEqual(self.frames[-1]['functionId'], snc.ConsumerFunction['PROCEED'])

	def test_invalid_generator_fails_before_sending(self):
		self.setup_target('dhw')
		self.values[(101, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID, None)] = 222
		self.scenario._run_external_test('pump')
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.frames, [])
		self.assert_clean()

	def test_failed_parameter_restore_marks_failure(self):
		self.setup_target('pool')
		write = self.scenario._write
		def fail_priority_restore(program_type, parameter_id, value):
			if (program_type == snc.ProgramType.CONSUMER
					and parameter_id == snc.ConsumerParameterId.PRIORITY and value == 1):
				raise RuntimeError('write failure')
			return write(program_type, parameter_id, value)
		self.scenario._write = fail_priority_restore
		self.scenario._run_external_test('pool')
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_clean()
		self.assertTrue(self.errors.called)

	def test_long_requests_are_refreshed_and_proceed_uses_same_sender(self):
		self.setup_target('dhw')
		self.scenario._generator_id = 102
		self.scenario._active_priority = None
		self.scenario._cooling = False
		with patch.object(self.base.time, 'monotonic', side_effect=(0, 11, 11, 12)):
			self.scenario._priority(9)
			self.scenario._refresh()
			self.scenario._priority()
		self.assertEqual([frame['functionId'] for frame in self.frames], [
			snc.ConsumerFunction['GIVE_WAY'], snc.ConsumerFunction['GIVE_WAY'],
			snc.ConsumerFunction['PROCEED']])
		self.assertTrue(all(frame['programId'] == 0 and frame['request'] == snc.RequestFlag.REQUEST
			and frame['data'] == [250, 9, 102] for frame in self.frames))
		self.frames.clear()
		with patch.object(self.base.time, 'monotonic', side_effect=(0, 11, 11, 12)):
			self.scenario._priority(9, generator_id=201)
			self.scenario._refresh()
			self.scenario._priority()
		self.assertTrue(all(frame['data'] == [250, 9, 201] for frame in self.frames))


if __name__ == '__main__':
	unittest.main()
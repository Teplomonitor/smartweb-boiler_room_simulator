"""Scenario contract tests with scripted CAN feedback, NOT firmware integration."""

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


parent = ModuleType('scenario.scenario')
parent.Scenario = object
main_thread = ModuleType('mainThread')
main_thread.taskEnable = lambda: True
with patch.dict(sys.modules, {'scenario.scenario': parent, 'mainThread': main_thread}):
	from smartnet.message import Message, CanListener
	from smartnet.remoteControl import RemoteControlParameter
	from smartnet.cascade_monitor import CascadeMonitor, PowerCommand, OutputReport
	from smartnet.channelMapping import InputChannel, OutputChannel, ChannelMapping
	from presets.cascade_test import build_cascade_test
	base = load_module('dispatch_parent', 'scenario/base/cascade_manager.py')
	with patch.dict(sys.modules, {'scenario.base.cascade_manager': base}):
		dispatch = load_module('dispatch_test_base', 'scenario/base/cascade_dispatch.py')
	with patch.dict(sys.modules, {'scenario.base.cascade_dispatch': dispatch}):
		SCENARIOS = [load_module(f'dispatch_case_{index}',
			f'scenario/list/cascade_manager/scenario_cascade_manager_3_6_3_{index}.py').Scenario
			for index in range(1, 13)]
	PRESETS = {count: load_module(f'dispatch_preset_{count}',
		f'presets/list/cascade_manager_{count}_boilers.py') for count in (2, 3, 4)}


def command_message(boiler_id=103, power=50, requester=102, temperature=50):
	encoded = int(temperature * 10).to_bytes(2, 'little', signed=True)
	return Message(snc.ProgramType.TEMPERATURE_SOURCE, boiler_id,
		snc.TemperatureSourceFunction['REQUEST_POWER'], snc.RequestFlag.REQUEST,
		[power, *encoded, requester])


class TestCascadeMonitor(unittest.TestCase):
	def setUp(self):
		self.monitor = CascadeMonitor(102, (103, 104), lambda: 123)

	def test_decode_and_filter(self):
		self.monitor.on_can_message_received(command_message(temperature=-12.3))
		self.monitor.on_can_message_received(command_message(boiler_id=199))
		self.assertEqual(self.monitor.snapshot()[0], [PowerCommand(123, 103, 50, -12.3)])

	def test_zero_padded_request_power(self):
		message = command_message(boiler_id=104, power=0)
		message.setData(b'\x00\x02\x80\x66\x00\x00\x00\x00')
		self.monitor.on_can_message_received(message)
		self.assertEqual(self.monitor.snapshot()[0], [PowerCommand(123, 104, 0, -3276.6)])

	def test_off_command_with_undefined_temperature(self):
		message = command_message(power=0)
		message.setData([0, 2, 128, 102])
		self.monitor.on_can_message_received(message)
		self.assertEqual(self.monitor.snapshot()[0], [PowerCommand(123, 103, 0, -3276.6)])

	def test_wrong_requester_and_bad_frames_fail_without_callback_exception(self):
		for data in ([50], [50, 0, 0, 102, 0], [101, 0, 0, 102],
			[50, 0, 0, 99], [50, 0, 0, 102, 0, 0, 0, 1], None):
			with self.subTest(data=data):
				monitor = CascadeMonitor(102, (103,))
				message = command_message()
				message.setData(data)
				monitor.on_can_message_received(message)
				self.assertIsNotNone(monitor.command_error)
				self.assertEqual(monitor.snapshot()[0], [])

	def test_output_reports_are_observed_independently_of_commands(self):
		self.monitor.on_can_message_received(Message(snc.ProgramType.REMOTE_CONTROL, 103,
			snc.RemoteControlFunction.GET_PARAMETER_VALUE, snc.RequestFlag.RESPONSE,
			[snc.ProgramType.PROGRAM, snc.ProgramParameterId.OUTPUT, 3, 0]))
		self.assertEqual(self.monitor.output_snapshot(), [OutputReport(123, 103, 3, 0)])
		self.assertEqual(self.monitor.snapshot()[0], [])
		self.monitor.on_can_message_received(Message(snc.ProgramType.REMOTE_CONTROL, 199,
			snc.RemoteControlFunction.GET_PARAMETER_VALUE, snc.RequestFlag.RESPONSE,
			[snc.ProgramType.PROGRAM, snc.ProgramParameterId.OUTPUT, 3, 255]))
		self.assertEqual(len(self.monitor.output_snapshot()), 1)

	def test_properties_decode(self):
		message = Message(snc.ProgramType.TEMPERATURE_SOURCE, 104,
			snc.TemperatureSourceFunction['GET_PROPERTIES'], snc.RequestFlag.RESPONSE,
			[1, 30, 0, 0, 0, 0, 1])
		self.monitor.on_can_message_received(message)
		self.assertEqual(self.monitor.snapshot()[1], {104: (123, 1)})
		message.setData(b'\x00\x0f\x00\x00\x00\x00\x00\x00')
		self.monitor.on_can_message_received(message)
		self.assertEqual(self.monitor.snapshot()[1], {104: (123, 0)})
		for data in ([1, 30, 0, 0, 0, 0, 1, 1], [1]):
			with self.subTest(data=data):
				monitor = CascadeMonitor(102, (104,))
				message.setData(data)
				monitor.on_can_message_received(message)
				with self.assertRaises(RuntimeError):
					monitor.snapshot()

	def test_unsubscribe_on_external_stop(self):
		with patch.object(CanListener, 'subscribe') as subscribe, patch.object(CanListener, 'unsubscribe') as unsubscribe:
			with self.assertRaises(InterruptedError):
				with self.monitor:
					raise InterruptedError()
			subscribe.assert_called_once_with(self.monitor)
			unsubscribe.assert_called_once_with(self.monitor)

	def test_command_history_is_bounded_without_failing_output_checks(self):
		for _ in range(self.monitor.HISTORY_SIZE + 1):
			self.monitor.on_can_message_received(command_message())
		self.assertEqual(len(self.monitor.snapshot()[0]), self.monitor.HISTORY_SIZE)

	def test_output_history_overflow_is_not_silently_ignored(self):
		message = Message(snc.ProgramType.REMOTE_CONTROL, 103,
			snc.RemoteControlFunction.GET_PARAMETER_VALUE, snc.RequestFlag.RESPONSE,
			[snc.ProgramType.PROGRAM, snc.ProgramParameterId.OUTPUT, 3, 0])
		for _ in range(self.monitor.HISTORY_SIZE + 1):
			self.monitor.on_can_message_received(message)
		with self.assertRaises(RuntimeError):
			self.monitor.output_snapshot()


class ScriptedFeedback:
	"""Only a test response source; deliberately supports injected defects."""
	def __init__(self, scenario_type):
		self.scenario = scenario_type()
		self.scenario._manualSensorsList = []
		self.now = 0
		self.scenario.clock = lambda: self.now
		self.scenario.wait = self.advance
		self.scenario.set_sensor_value = self.set_sensor
		self.scenario.request_output_states = self.request_outputs
		self.scenario.wait_state_permanence = lambda predicate, duration, timeout: self.discover(predicate, timeout)
		self.scenario._programList = {}
		self.sensors = []
		self.outputs = []
		self.programs = []
		for name in self.scenario.get_required_programs():
			program = Mock()
			self.scenario._programList[name] = program
			if name.startswith('boiler_'):
				index = len(self.programs)
				program.get_id.return_value = 103 + index
				inputs = {key: InputChannel() for key in ('temperature', 'backwardTemperature', 'outsideRequest')}
				inputs['error'] = self.sensor(index, 30)
				output = {key: OutputChannel() for key in ('burner1', 'burner2')}
				for channel_id, key in enumerate(('power', 'pump')):
					output[key] = OutputChannel(ChannelMapping(channel_id, 'CHANNEL_RELAY', 124 + index), 0,
						channelId=3 if key == 'power' else 0)
				self.outputs.extend((output['power'], output['pump']))
				program.get_input_channel.side_effect = inputs.__getitem__
				program.get_output_channel.side_effect = output.__getitem__
				program.get_power_output.return_value = output['power']
				program.get_pump.return_value = output['pump']
				program.get_power_output_percent.side_effect = lambda output=output: max(0, (output['power'].get_value() - 1) * 100 / 253)
				self.programs.append(program)
		self.collector = self.sensor(5, 30)
		self.dhw = self.sensor(6, 30)
		self.scenario._programList['cascade'].get_id.return_value = 102
		self.scenario._programList['cascade'].get_input_channel.return_value = self.collector
		self.scenario._programList['dhw'].get_id.return_value = 101
		self.scenario._programList['dhw'].get_temperature.return_value = self.dhw
		self.values = {(program.get_id(), kind, key): 1 for program, kind, key, value in self.scenario.settings()}
		self.original_values = self.values.copy()
		self.scenario.read_parameter = self.read
		self.scenario.write_parameter = self.write
		self.demand = None
		self.failed = None
		self.ready = {}
		self.last_power = {program.get_id(): 0 for program in self.programs}
		self.defect = None
		self.cancelled_start = None
		self.was_running = False
		self.pending_outputs = False
		self.last_signals = {}

	def request_outputs(self):
		self.pending_outputs = True

	def report_output(self, program, output, value):
		if self.defect == 'no_output_reports':
			return
		self.scenario.monitor.on_can_message_received(Message(
			snc.ProgramType.REMOTE_CONTROL, program.get_id(),
			snc.RemoteControlFunction.GET_PARAMETER_VALUE, snc.RequestFlag.RESPONSE,
			[snc.ProgramType.PROGRAM, snc.ProgramParameterId.OUTPUT, output.get_id(), value]))

	def sensor(self, channel_id, value):
		sensor = InputChannel(ChannelMapping(channel_id, 'CHANNEL_SENSOR', 123), value)
		self.sensors.append(sensor)
		return sensor

	def set_sensor(self, sensor, value):
		sensor.set_manual(True)
		sensor.set_value(value, True)
		if sensor not in self.scenario._manualSensorsList:
			self.scenario._manualSensorsList.append(sensor)

	def discover(self, predicate, timeout):
		for _ in range(timeout):
			self.advance(1)
			if predicate():
				return True
		return False

	def read(self, program, kind, key, index=None):
		if kind == snc.ProgramType.CASCADE_MANAGER:
			if key == snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID:
				return 103 + index
			if key == snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_POWER:
				return 30
			if key == snc.CascadeManagerParameterId.REQUIRED_POWER:
				return self.demand
		if kind == snc.ProgramType.TEMPERATURE_SOURCE:
			if key == snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE:
				return 50
			if key == snc.TemperatureSourceParameterId.ERROR_STATE:
				if self.defect == 'first_only_error':
					return int(103 in (self.failed or ()))
				return int(len(self.failed or ()) == len(self.programs))
		return self.values[(program.get_id(), kind, key)]

	def write(self, program, kind, key, value):
		self.values[(program.get_id(), kind, key)] = value

	def advance(self, seconds):
		self.now += seconds
		if self.defect == 'stop':
			raise InterruptedError('external stop')
		monitor = self.scenario.monitor
		demand = round(max(0, min(100, (50 - self.collector.get_value()) * 5)))
		failed = {program.get_id() for program in self.programs if program.get_input_channel('error').isShort()}
		if self.defect == 'stop_on_fault' and failed:
			raise InterruptedError('external stop with active alarm')
		if demand != self.demand or failed != self.failed:
			if (self.defect == 'cancelled_start' and self.demand is not None
				and demand < self.demand and self.cancelled_start is None):
				pending = [ready for key, ready in self.ready.items()
					if ready > self.now and not self.last_power[key]]
				if pending:
					self.cancelled_start = min(pending)
			fault_change = failed != self.failed
			self.demand, self.failed = demand, failed
			remaining = len(self.programs) * demand
			rank = 0
			self.target = {}
			for program in self.programs:
				key = program.get_id()
				power = 0 if key in failed else min(100, remaining)
				remaining -= power
				self.target[key] = power
				if power and not self.last_power[key]:
					if key != min(set(self.last_power) - failed):
						rank += 1
					delay = 60 * self.scenario.DELAY_MINUTES * rank
					if fault_change and self.defect != 'fault_delay':
						delay = 0
					if fault_change and failed and self.defect == 'fault_delay':
						delay = 60
					if self.defect == 'early':
						delay = 0
					self.ready[key] = self.now + delay
		for program in self.programs:
			key = program.get_id()
			monitor.on_can_message_received(Message(snc.ProgramType.TEMPERATURE_SOURCE, key,
				snc.TemperatureSourceFunction['GET_PROPERTIES'], snc.RequestFlag.RESPONSE,
				[1, 30, 0, 0, 0, 0, int(key in failed), 0]))
			power = self.target[key] if self.now >= self.ready.get(key, 0) else 0
			if self.defect == 'no_replacement' and failed:
				power = 0
			if self.defect == 'fault_power' and key in failed:
				power = 50
			if self.defect == 'wrong_distribution':
				power = self.target[103 + (key - 102) % len(self.programs)]
			if (self.defect == 'transient_early' and self.target[key]
				and self.now < self.ready.get(key, 0)):
				monitor.on_can_message_received(command_message(key, 50))
				self.report_output(program, program.get_power_output(), 128)
			if (self.defect == 'cancelled_start' and key == 104
				and self.cancelled_start is not None and self.now >= self.cancelled_start):
				monitor.on_can_message_received(command_message(key, 50))
				self.report_output(program, program.get_power_output(), 128)
			missing = self.defect == 'missing' or (
				self.defect == 'missing_stop' and self.was_running and demand == 0)
			if not missing:
				message = command_message(
					199 if self.defect == 'address' else key, round(power),
					99 if self.defect == 'requester' else 102,
					40 if self.defect == 'temperature' else 50)
				message.setData([*message.get_data(), 0, 0, 0, 0])
				monitor.on_can_message_received(message)
			self.last_power[key] = power
			signal = 0 if power == 0 else round(1 + 253 * power / 100)
			if self.defect == 'stuck_output' and demand == 0:
				signal = 200
			program.get_power_output().set_value(signal)
			program.get_pump().set_value(0 if self.defect == 'pump' else (255 if power else 0))
			for output in (program.get_power_output(), program.get_pump()):
				identity = (key, output.get_id())
				if self.pending_outputs or self.last_signals.get(identity) != output.get_value():
					self.report_output(program, output, output.get_value())
				self.last_signals[identity] = output.get_value()
		self.pending_outputs = False
		self.was_running = self.was_running or demand > 0

	def run(self):
		with patch.object(CanListener, 'subscribe'), patch.object(CanListener, 'unsubscribe') as unsubscribe:
			try:
				self.scenario.run()
			finally:
				unsubscribe.assert_called_once()

	def assert_restored(self, testcase, status):
		testcase.assertEqual(self.scenario._status, status)
		testcase.assertEqual(self.values, self.original_values)
		testcase.assertEqual([sensor.get_value() for sensor in self.sensors], [30] * len(self.sensors))
		testcase.assertFalse(any(sensor.isManual() or sensor.isShort() or sensor.isOpen() for sensor in self.sensors))
		testcase.assertEqual(self.scenario._manualSensorsList, [])


class TestDispatchScenarios(unittest.TestCase):
	def setUp(self):
		for name in ('print_log', 'print_error'):
			patcher = patch.object(dispatch, name)
			patcher.start()
			self.addCleanup(patcher.stop)

	def test_all_twelve_scripted_success_paths(self):
		for scenario_type in SCENARIOS:
			with self.subTest(checklist=scenario_type.get_checklist_id(None)):
				feedback = ScriptedFeedback(scenario_type)
				feedback.run()
				feedback.assert_restored(self, 'OK')

	def test_output_probes_do_not_wait_for_responses(self):
		feedback = ScriptedFeedback(SCENARIOS[0])
		sent = []
		def capture(message, *args, **kwargs):
			sent.append((message, args, kwargs))
		with patch.object(Message, 'send', new=capture):
			dispatch.CascadeDispatchScenario.request_output_states(feedback.scenario)
		self.assertEqual([(msg.getProgramId(), msg.get_data()[-1]) for msg, _, _ in sent],
			[(103, 3), (103, 0), (104, 3), (104, 0)])
		self.assertTrue(all(msg.getRequestFlag() == snc.RequestFlag.REQUEST for msg, _, _ in sent))
		self.assertTrue(all(not args and not kwargs for _, args, kwargs in sent))

	def test_stage_delay_is_encoded_as_four_byte_time(self):
		feedback = ScriptedFeedback(SCENARIOS[3])
		delay_setting = next(value for _, kind, key, value in feedback.scenario.settings()
			if kind == snc.ProgramType.CASCADE_MANAGER
			and key == snc.CascadeManagerParameterId.NEXT_TEMPERATURE_SRC_ON_DELAY)
		self.assertEqual(delay_setting, 60)
		parameter = RemoteControlParameter(programType=snc.ProgramType.CASCADE_MANAGER,
			parameterId=snc.CascadeManagerParameterId.NEXT_TEMPERATURE_SRC_ON_DELAY,
			parameterValue=delay_setting, programId=102)
		self.assertEqual(parameter.getParameterType(), 'TIME_MS')
		self.assertEqual(parameter.getParameterSize(), 4)
		self.assertEqual(parameter.valueToData(delay_setting), [0x60, 0xea, 0, 0])
		self.assertEqual(parameter.dataToValue([0x60, 0xea, 0, 0]), 60)

	def test_confirmed_fault_rejects_nonzero_manager_command(self):
		feedback = ScriptedFeedback(SCENARIOS[6])
		feedback.scenario.monitor = CascadeMonitor(102, (103, 104), feedback.scenario.clock)
		feedback.scenario._fault_confirmations = {103: 0}
		feedback.now = feedback.scenario.REPLACEMENT_TIMEOUT + 1
		feedback.scenario.monitor.on_can_message_received(command_message(103, 50))
		with self.assertRaisesRegex(RuntimeError, 'запрашивает 50% у аварийного котла 103'):
			feedback.scenario.fault_guard()

	def test_broken_boiler_outputs_fail(self):
		for defect in ('stuck_output', 'wrong_distribution', 'pump', 'no_output_reports'):
			with self.subTest(defect=defect):
				feedback = ScriptedFeedback(SCENARIOS[0])
				feedback.defect = defect
				feedback.run()
				feedback.assert_restored(self, 'FAIL')

	def test_timeout_identifies_failed_dispatch_check(self):
		for defect, reason in (('no_output_reports', 'нет подтверждения'),
			('stuck_output', 'выход'), ('pump', 'насос')):
			with self.subTest(defect=defect):
				feedback = ScriptedFeedback(SCENARIOS[0])
				feedback.defect = defect
				with patch.object(dispatch, 'print_error') as log:
					feedback.run()
				feedback.assert_restored(self, 'FAIL')
				timeouts = [str(call.args[0]) for call in log.call_args_list if 'Тайм-аут:' in str(call.args[0])]
				self.assertEqual(len(timeouts), 1)
				self.assertIn(reason, timeouts[0])
				self.assertIn('коллектор=', timeouts[0])
				self.assertIn('последние отчёты выходов', timeouts[0])

	def test_command_defects_do_not_define_output_only_success(self):
		for defect in ('missing', 'requester', 'address', 'temperature', 'missing_stop'):
			with self.subTest(defect=defect):
				feedback = ScriptedFeedback(SCENARIOS[0])
				feedback.defect = defect
				feedback.run()
				feedback.assert_restored(self, 'OK')

	def test_early_stage_is_rejected(self):
		for scenario_type in SCENARIOS[3:6]:
			for defect in ('early', 'transient_early', 'cancelled_start'):
				with self.subTest(checklist=scenario_type.get_checklist_id(None), defect=defect):
					feedback = ScriptedFeedback(scenario_type)
					feedback.defect = defect
					feedback.run()
					feedback.assert_restored(self, 'FAIL')
					if defect == 'cancelled_start':
						self.assertIsNotNone(feedback.cancelled_start)

	def test_broken_fault_handling_is_rejected(self):
		for defect in ('no_replacement', 'fault_power', 'fault_delay', 'first_only_error'):
			with self.subTest(defect=defect):
				feedback = ScriptedFeedback(SCENARIOS[9])
				feedback.defect = defect
				feedback.run()
				feedback.assert_restored(self, 'FAIL')

	def test_external_stop_restores_all_inputs_and_parameters(self):
		for defect in ('stop', 'stop_on_fault'):
			with self.subTest(defect=defect):
				feedback = ScriptedFeedback(SCENARIOS[9])
				feedback.defect = defect
				with self.assertRaises(InterruptedError):
					feedback.run()
				feedback.assert_restored(self, 'FAIL')

	def test_unconfirmed_outputs_cannot_pass_with_correct_cached_values(self):
		feedback = ScriptedFeedback(SCENARIOS[0])
		feedback.run()
		self.assertFalse(feedback.scenario.commands_match(
			feedback.scenario.expected_powers(0), feedback.now + 1))

	def test_existing_manual_alarm_state_is_restored(self):
		feedback = ScriptedFeedback(SCENARIOS[9])
		sensor = feedback.programs[0].get_input_channel('error')
		feedback.set_sensor(sensor, 'short')
		feedback.run()
		self.assertEqual(feedback.scenario._status, 'OK')
		self.assertTrue(sensor.isShort())
		self.assertTrue(sensor.isManual())
		self.assertIn(sensor, feedback.scenario._manualSensorsList)
		self.assertEqual(feedback.values, feedback.original_values)

	def test_presets_and_ids_match_matrix(self):
		checklists = set()
		for scenario_type in SCENARIOS:
			scenario = scenario_type()
			checklists.add(scenario.get_checklist_id())
			preset = PRESETS[scenario.BOILER_COUNT]
			self.assertEqual(scenario.get_default_preset(), f'cascade_manager_{scenario.BOILER_COUNT}_boilers')
			programs, controllers = preset.get_presets_list()
			self.assertEqual(len(programs), scenario.BOILER_COUNT + 2)
			self.assertEqual(len(controllers), scenario.BOILER_COUNT + 1)
			self.assertEqual([p.get_id() for p in programs[2:]], programs[1].getSettings().getSourceList()[:scenario.BOILER_COUNT])
			mappings = []
			for program in programs:
				for mapping in program.get_inputs() + program.get_outputs():
					if mapping.is_mapped():
						self.assertLess(mapping.get_channel_id(), 6 if mapping.get_channel_type() == 'CHANNEL_SENSOR' else 8)
						mappings.append(mapping.get_raw())
			self.assertEqual(len(mappings), len(set(mappings)))
		self.assertEqual(len(checklists), 12)
		with self.assertRaises(ValueError):
			build_cascade_test(1)


if __name__ == '__main__':
	unittest.main()
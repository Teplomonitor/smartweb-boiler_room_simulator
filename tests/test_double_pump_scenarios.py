import unittest
from unittest.mock import Mock, call, patch

# Import in application order to avoid the mainThread/message import cycle.
import mainThread  # noqa: F401
from presets.preset import get_presets_list
from programs.double_pump import DoublePump
from scenario.base.double_pump import DoublePumpScenario
from scenario.list.doublePump.scenario_double_pump_3_8_2 import Scenario as ControlScenario
from scenario.list.doublePump.scenario_double_pump_3_8_3 import Scenario as FaultScenario
from scenario.scenario import ThreadStoppedException
import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter


class DoublePumpScenarioTests(unittest.TestCase):
	def make_scenario(self, scenario_type=ControlScenario, preset='double_pump_discrete'):
		presets, _ = get_presets_list(preset)
		with patch('programs.program.Program.read_output', return_value=0):
			pump = DoublePump(presets[0])
		self.addCleanup(pump.clear)
		pump.read_parameter_value = Mock(return_value=0)
		pump.write_parameter = Mock(return_value=True)
		pump.read_output = Mock(return_value=0)
		# Skip application startup: these tests exercise scenario logic with mocked I/O.
		scenario = scenario_type.__new__(scenario_type)
		scenario._programList = {'double_pump': pump}
		scenario.wait = Mock(return_value=True)
		scenario.simple_wait = Mock(return_value=True)
		scenario.check_state = Mock(return_value=True)
		scenario._clear_test_faults = Mock()
		return scenario, pump

	@staticmethod
	def sensor_snapshot(pump):
		return [
			(sensor.get_value(), sensor.isManual(), sensor.isOpen(), sensor.isShort())
			for sensor in pump.get_inputs().values()
		]

	def test_control_sequence_repeats_start_and_stop_for_both_presets(self):
		for preset in ('double_pump_discrete', 'double_pump_analog'):
			with self.subTest(preset=preset):
				scenario, pump = self.make_scenario(preset=preset)
				observed = []
				def check(predicate, description):
					observed.append((predicate.__name__, pump.get_input_channel('control').isShort()))
					return True
				scenario.check_state.side_effect = check
				scenario.run()
				self.assertEqual(scenario._status, 'OK')
				self.assertEqual(observed, [
					('_healthy_and_off', False), ('one_pump_is_on', True),
					('pumps_are_off', False), ('one_pump_is_on', True), ('pumps_are_off', False),
				])
				scenario._clear_test_faults.assert_called_once()

	def test_fault_sequence_keeps_control_active_and_holds_both_faults(self):
		scenario, pump = self.make_scenario(FaultScenario)
		def hold(predicate, duration):
			self.assertEqual(predicate.__name__, 'both_pumps_failed_and_off')
			self.assertEqual(duration, scenario.FAULT_HOLD_DURATION)
			for name in ('control', 'pump_1_error', 'pump_2_error'):
				self.assertTrue(pump.get_input_channel(name).isShort())
			return True
		scenario.wait_state_permanence = Mock(side_effect=hold)
		scenario.run()
		self.assertEqual(scenario._status, 'OK')
		scenario.wait_state_permanence.assert_called_once()

	def test_failure_timeout_and_cancellation_restore_inputs_and_settings(self):
		for outcome in ('success', 'failure', 'exception', 'cancel'):
			with self.subTest(outcome=outcome):
				scenario, pump = self.make_scenario()
				pump.get_input_channel('control').set_value(42)
				pump.get_input_channel('control').set_manual(True)
				pump.get_input_channel('flow').set_value('short')
				pump.get_input_channel('flow').set_manual(True)
				before = self.sensor_snapshot(pump)
				settings = {'alarm_status': 0, 'double_power': 1, 'training_enabled': 1, 'manual_mode_enabled': 1}
				pump.read_parameter_value.side_effect = settings.get
				def sequence():
					scenario._set_input('pump_1_error', 'short')
					scenario._set_input('pump_2_error', 'short')
					if outcome == 'exception':
						raise RuntimeError('I/O failed')
					if outcome == 'cancel':
						raise ThreadStoppedException('cancelled')
					return outcome == 'success'
				if outcome in ('exception', 'cancel'):
					with self.assertRaises((RuntimeError, ThreadStoppedException)):
						scenario.run_pump_test(sequence)
				else:
					scenario.run_pump_test(sequence)
				self.assertEqual(scenario._status, 'OK' if outcome == 'success' else 'FAIL')
				self.assertEqual(self.sensor_snapshot(pump), before)
				scenario._clear_test_faults.assert_called_once()
				self.assertEqual(pump.write_parameter.call_args_list[-3:], [
					call('manual_mode_enabled', 1), call('training_enabled', 1), call('double_power', 1),
				])

	def test_missing_mapping_or_parameter_aborts_before_modifications(self):
		for problem in ('mapping', 'parameter', 'active_fault', 'unknown_alarm'):
			with self.subTest(problem=problem):
				scenario, pump = self.make_scenario()
				if problem == 'mapping':
					pump.get_output_channel('discrete_pump_2').set_mapping(None)
				elif problem == 'active_fault':
					pump.get_input_channel('pump_2_error').set_value('short')
				else:
					pump.read_parameter_value.side_effect = lambda name: None if (
						name == ('double_power' if problem == 'parameter' else 'alarm_status')
					) else 0
				before = self.sensor_snapshot(pump)
				sequence = Mock(return_value=True)
				scenario.run_pump_test(sequence)
				self.assertEqual(scenario._status, 'FAIL')
				self.assertEqual(self.sensor_snapshot(pump), before)
				pump.write_parameter.assert_not_called()
				sequence.assert_not_called()

	def test_failed_setting_write_is_restored_and_sequence_not_run(self):
		scenario, pump = self.make_scenario()
		pump.write_parameter.side_effect = [False, True]
		before = self.sensor_snapshot(pump)
		sequence = Mock()
		scenario.run_pump_test(sequence)
		self.assertEqual(scenario._status, 'FAIL')
		sequence.assert_not_called()
		self.assertEqual(self.sensor_snapshot(pump), before)
		self.assertEqual(pump.write_parameter.call_args_list, [call('double_power', 0), call('double_power', 0)])

	def test_cleanup_failure_marks_failure_but_still_restores_settings_and_inputs(self):
		scenario, pump = self.make_scenario()
		scenario._clear_test_faults.side_effect = RuntimeError('reset failed')
		before = self.sensor_snapshot(pump)
		scenario.run_pump_test(lambda: True)
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(self.sensor_snapshot(pump), before)
		self.assertEqual(pump.write_parameter.call_args_list[-1], call('double_power', 0))

	def test_output_checks_require_known_values_for_each_mapped_output(self):
		for preset in ('double_pump_discrete', 'double_pump_analog'):
			with self.subTest(preset=preset):
				scenario, pump = self.make_scenario(preset=preset)
				scenario.run_pump_test(lambda: True)
				for values, off, one_on in (([0, 0], True, False), ([254, 0], False, True),
						([0, 255], False, True), ([255, 255], False, False), ([None, 0], False, False)):
					pump.read_output.side_effect = values
					self.assertEqual(scenario.pumps_are_off(), off)
					pump.read_output.side_effect = values
					self.assertEqual(scenario.one_pump_is_on(), one_on)

	def test_fault_predicate_requires_both_statuses_alarm_and_stopped_outputs(self):
		scenario, pump = self.make_scenario(FaultScenario)
		scenario.run_pump_test(lambda: True)
		for statuses, outputs, expected in (
			([1, 1], [255, 0, 0], True), ([0, 1], [], False), ([1, None], [], False),
			([1, 1], [0], False), ([1, 1], [255, 255, 0], False), ([1, 1], [255, None], False),
		):
			pump.read_parameter_value.side_effect = statuses
			pump.read_output.side_effect = outputs
			self.assertEqual(scenario.both_pumps_failed_and_off(), expected)

	def test_real_cleanup_uses_noninterruptible_wait_and_resets_after_opening_inputs(self):
		scenario, pump = self.make_scenario()
		scenario.run_pump_test(lambda: True)
		for name in ('control', 'pump_1_error', 'pump_2_error'):
			scenario._set_input(name, 'short')
		scenario._healthy_and_off = Mock(side_effect=[False, True])
		scenario.wait.side_effect = ThreadStoppedException('cancelled')
		DoublePumpScenario._clear_test_faults(scenario)
		for name in ('control', 'pump_1_error', 'pump_2_error'):
			self.assertTrue(pump.get_input_channel(name).isOpen())
		self.assertEqual(scenario.simple_wait.call_args_list, [
			call(scenario.INPUT_SETTLE_DURATION), call(scenario.CLEANUP_POLL_INTERVAL),
		])
		self.assertEqual(pump.write_parameter.call_args, call('alarm_status', 0))

	def test_cleanup_timeout_is_bounded(self):
		scenario, _ = self.make_scenario()
		scenario.run_pump_test(lambda: True)
		scenario._healthy_and_off = Mock(return_value=False)
		with patch('scenario.base.double_pump.time.monotonic', side_effect=[0, scenario.STATE_TIMEOUT]):
			with self.assertRaises(RuntimeError):
				DoublePumpScenario._clear_test_faults(scenario)

	def test_parameter_codes_and_wire_values_match_firmware(self):
		_, pump = self.make_scenario()
		for name, parameter_id in (('pump_1_status', 1), ('pump_2_status', 2), ('double_power', 3), ('alarm_status', 7)):
			code = pump.get_parameter_code(name)
			self.assertEqual(code, (snc.ProgramType.DOUBLE_PUMP, parameter_id))
			parameter = RemoteControlParameter(parameterCode=code, programId=pump.get_id())
			self.assertEqual(parameter.getParameterType(), 'UINT8_T')
			self.assertEqual(parameter.valueToData(1), [1])
			self.assertEqual(parameter.dataToValue([0]), 0)
		self.assertEqual(pump.get_parameter_code('training_enabled'), (snc.ProgramType.PROGRAM, 7))
		self.assertEqual(pump.get_parameter_code('manual_mode_enabled'), (snc.ProgramType.PROGRAM, 8))
		self.assertIsNone(pump.get_parameter_code('unknown'))


if __name__ == '__main__':
	unittest.main()
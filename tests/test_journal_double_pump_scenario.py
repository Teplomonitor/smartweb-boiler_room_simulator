import unittest
from unittest.mock import Mock, call, patch

# Import in application order to avoid the mainThread/message import cycle.
import mainThread  # noqa: F401
from presets.preset import get_presets_list
from programs.double_pump import DoublePump
from scenario.base.double_pump import DoublePumpScenario
from scenario.list.journal.scenario_journal_9_27 import Scenario
from scenario.scenario import ThreadStoppedException
import smartnet.constants as snc
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class JournalDoublePumpScenarioTests(unittest.TestCase):
	def make_scenario(self):
		presets, _ = get_presets_list('double_pump_discrete')
		with patch('programs.program.Program.read_output', return_value=0):
			pump = DoublePump(presets[0])
		self.addCleanup(pump.clear)
		pump.read_parameter_value = Mock(return_value=0)
		pump.write_parameter = Mock(return_value=True)
		pump.read_output = Mock(return_value=0)
		scenario = Scenario.__new__(Scenario)
		scenario._programList = {'double_pump': pump}
		scenario.wait = Mock(return_value=True)
		scenario.simple_wait = Mock(return_value=True)
		scenario.check_state = Mock(return_value=True)
		scenario.wait_event = Mock(return_value=True)
		scenario.snapshot_journal = Mock(return_value=True)
		scenario.wait_journal_entry = Mock(return_value=True)
		scenario._clear_test_faults = Mock()
		return scenario, pump

	@staticmethod
	def sensor_snapshot(pump):
		return [(sensor.get_value(), sensor.isManual(), sensor.isOpen(), sensor.isShort())
			for sensor in pump.get_inputs().values()]

	def test_metadata_and_preset(self):
		scenario, pump = self.make_scenario()
		self.assertEqual(scenario.get_checklist_id(), '9.27')
		self.assertEqual(scenario.get_default_preset(), 'double_pump_discrete')
		self.assertEqual(scenario.get_required_programs(), {'double_pump': snc.ProgramType.DOUBLE_PUMP})
		self.assertEqual(pump.get_type(), snc.ProgramType.DOUBLE_PUMP)
		self.assertTrue(scenario.force_preset_load())

	def test_three_independent_faults_use_fresh_snapshots_and_matching_codes(self):
		scenario, pump = self.make_scenario()
		scenario._pump_states = Mock(return_value=[True, False])
		observed = []
		def snapshot():
			self.assertTrue(pump.get_input_channel('pump_1_error').isOpen())
			self.assertTrue(pump.get_input_channel('pump_2_error').isOpen())
			return True
		def read_entry(*args):
			observed.append(tuple(pump.get_input_channel(name).isShort()
				for name in ('pump_1_error', 'pump_2_error')))
			return True
		def reset():
			for name in ('control', 'pump_1_error', 'pump_2_error'):
				scenario._set_input(name, 'open')
		scenario.snapshot_journal.side_effect = snapshot
		scenario.wait_journal_entry.side_effect = read_entry
		scenario._clear_test_faults.side_effect = reset
		before = self.sensor_snapshot(pump)
		scenario.run()
		self.assertEqual(scenario._status, 'OK')
		self.assertEqual(observed, [(True, False), (False, True), (False, False)])
		self.assertEqual(scenario.snapshot_journal.call_count, 3)
		self.assertEqual(scenario.wait_journal_entry.call_args_list, [call(
			MessageLogCode.MLC_DOUBLE_PUMP_FAILURE, SeverityCode.SC_CRITICAL,
			pump.get_id(), scenario.JOURNAL_TIMEOUT,
		)] * 3)
		self.assertEqual(scenario.wait.call_args_list.count(call(scenario.FAULT_INPUT_DURATION)), 2)
		self.assertEqual(scenario._clear_test_faults.call_count, 3)
		self.assertEqual(self.sensor_snapshot(pump), before)

	def test_flow_is_manual_open_until_fault_then_automatic_for_reserve_pump(self):
		for states, index in (([True, False], 1), ([False, True], 2)):
			with self.subTest(index=index):
				scenario, pump = self.make_scenario()
				scenario._pump = pump
				scenario._pump_states = Mock(return_value=states)
				def wait_fault(predicate, timeout):
					self.assertTrue(pump.get_input_channel('flow').isManual())
					self.assertTrue(pump.get_input_channel('flow').isOpen())
					self.assertTrue(pump.get_input_channel('control').isShort())
					self.assertEqual(timeout, scenario.FLOW_FAILURE_DELAY + scenario.FLOW_TIMEOUT_MARGIN)
					scenario._pump_has_fault = Mock(return_value=True)
					self.assertTrue(predicate())
					scenario._pump_has_fault.assert_called_once_with(index)
					return True
				scenario.wait_event.side_effect = wait_fault
				scenario.wait_journal_entry.side_effect = lambda *args: not pump.get_input_channel('flow').isManual()
				self.assertTrue(scenario._check_missing_flow())

	def test_failure_or_cancellation_restores_all_inputs_and_settings(self):
		for outcome in ('journal', 'snapshot', 'cancel', 'exception', 'flow_timeout', 'unknown_outputs'):
			with self.subTest(outcome=outcome):
				scenario, pump = self.make_scenario()
				pump.get_input_channel('flow').set_value('short')
				pump.get_input_channel('flow').set_manual(True)
				before = self.sensor_snapshot(pump)
				pump.read_parameter_value.side_effect = lambda name: 0 if name == 'alarm_status' else 1
				scenario._pump_states = Mock(return_value=[True, False])
				if outcome == 'journal':
					scenario.wait_journal_entry.return_value = False
				elif outcome == 'snapshot':
					scenario.snapshot_journal.return_value = False
				elif outcome in ('cancel', 'exception'):
					scenario.wait_journal_entry.side_effect = (
						ThreadStoppedException('cancelled') if outcome == 'cancel' else RuntimeError('I/O failed'))
				elif outcome == 'flow_timeout':
					scenario.wait_event.return_value = False
				else:
					scenario._pump_states.return_value = None
				if outcome in ('cancel', 'exception'):
					with self.assertRaises((ThreadStoppedException, RuntimeError)):
						scenario.run()
				else:
					scenario.run()
				self.assertEqual(scenario._status, 'FAIL')
				self.assertEqual(self.sensor_snapshot(pump), before)
				self.assertEqual(pump.write_parameter.call_args_list[-3:], [
					call('manual_mode_enabled', 1), call('training_enabled', 1), call('double_power', 1),
				])
				self.assertGreaterEqual(scenario._clear_test_faults.call_count, 1)
				if outcome == 'snapshot':
					scenario.wait_journal_entry.assert_not_called()

	def test_real_cleanup_clears_faults_after_cancellation_with_manual_flow(self):
		scenario, pump = self.make_scenario()
		scenario._clear_test_faults = lambda: DoublePumpScenario._clear_test_faults(scenario)
		before = self.sensor_snapshot(pump)
		def cancel_with_active_inputs():
			for name in ('control', 'pump_1_error', 'pump_2_error'):
				scenario._set_input(name, 'short')
			scenario._set_input('flow', 'open')
			raise ThreadStoppedException('cancelled')
		scenario._check_journal_faults = cancel_with_active_inputs
		with self.assertRaises(ThreadStoppedException):
			scenario.run()
		for name in ('control', 'pump_1_error', 'pump_2_error'):
			self.assertTrue(pump.get_input_channel(name).isOpen())
		self.assertEqual(self.sensor_snapshot(pump), before)
		self.assertIn(call('alarm_status', 0), pump.write_parameter.call_args_list)
		self.assertEqual(scenario._status, 'FAIL')

	def test_fault_predicate_requires_known_status_and_active_alarm(self):
		scenario, pump = self.make_scenario()
		scenario._pump = pump
		for status, alarm, expected in ((None, 255, False), (0, 255, False),
				(1, None, False), (1, 0, False), (1, 255, True)):
			pump.read_parameter_value.return_value = status
			pump.read_output.return_value = alarm
			scenario._alarm = pump.get_output_channel('alarm')
			self.assertEqual(scenario._pump_has_fault(2), expected)

	def test_missing_parameter_or_failed_write_prevents_journal_checks(self):
		for problem in ('read', 'write'):
			with self.subTest(problem=problem):
				scenario, pump = self.make_scenario()
				if problem == 'read':
					pump.read_parameter_value.side_effect = lambda name: None if name == 'training_enabled' else 0
				else:
					pump.write_parameter.return_value = False
				before = self.sensor_snapshot(pump)
				scenario.run()
				self.assertEqual(scenario._status, 'FAIL')
				self.assertEqual(self.sensor_snapshot(pump), before)
				scenario.snapshot_journal.assert_not_called()

	def test_cleanup_failure_overrides_success(self):
		scenario, pump = self.make_scenario()
		scenario._check_journal_faults = Mock(return_value=True)
		scenario._clear_test_faults.side_effect = RuntimeError('reset failed')
		before = self.sensor_snapshot(pump)
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(self.sensor_snapshot(pump), before)


if __name__ == '__main__':
	unittest.main()
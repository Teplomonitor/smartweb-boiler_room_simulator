from contextlib import contextmanager
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scenario.base.journal_temperature import JournalTemperatureScenario
from scenario.list.journal.scenario_journal_9_16_and_9_17 import Scenario as ModerateScenario
from scenario.list.journal.scenario_journal_9_18_and_9_19 import Scenario as SevereScenario
from scenario.scenario import Scenario, ScenarioThread, ThreadStoppedException
from presets.list.journal_underheating import get_presets_list as moderate_preset
from presets.list.journal_low_temperature import get_presets_list as severe_preset
import smartnet.constants as snc
from smartnet.message_log_constants import MessageLogCode as Code, SeverityCode as Severity
from smartnet.parameter_registry import get_parameter


def make_programs(scenario):
	programs = {}
	for index, (name, kind) in enumerate(scenario.get_required_programs().items(), 101):
		program = Mock()
		program.get_id.return_value = index
		program.get_type.return_value = kind
		channels = {}
		def input_channel(key, channels=channels):
			if key not in channels:
				sensor = Mock()
				sensor.get_value.return_value = 22
				sensor.isManual.return_value = False
				sensor.isShort.return_value = False
				sensor.isOpen.return_value = False
				sensor.is_mapped.return_value = True
				channels[key] = sensor
			return channels[key]
		program.get_input_channel.side_effect = input_channel
		programs[name] = program
	return programs


class TemperatureRun:
	"""Synthetic journal transport and clock, not a simulator of controller logic."""
	def __init__(self, scenario_class, omitted=(), early=(), intermediate_recovery=False,
			wrong_severity=(), cleanup_error=False, simultaneous=False):
		self.now = 100.0
		self.sent = set()
		self.changes = []
		self.cursors = []
		self.cleaned = False
		self.scenario = scenario_class.__new__(scenario_class)
		s = self.scenario
		s._programList = make_programs(s)
		s._manualSensorsList = []
		s.clock = lambda: self.now
		s.wait = self.wait
		s.wait_event = lambda condition, timeout: condition()
		s.input_is = Mock(return_value=True)
		s.validate_operating_state = Mock()
		if simultaneous:
			s.HALF_HOUR = s.ONE_HOUR
		self.checks = s.make_checks()
		s.make_checks = lambda: self.checks

		@contextmanager
		def configuration(checks):
			try:
				yield
			finally:
				self.cleaned = True
				if cleanup_error:
					s._cleanup_failed = True
					raise RuntimeError('restoration failed')
		s.temperature_configuration = configuration
		s.snapshot_journal = self.snapshot
		s.change_temperature = self.change

		def read(cursor):
			self.cursors.append(cursor)
			entries = []
			for check in self.checks:
				key = (check.name, 'cold')
				due = check.changed_at + check.delay + (1 if check.name not in early else -30)
				if check.phase == 'cold' and key not in self.sent and self.now >= due:
					self.sent.add(key)
					if key not in omitted:
						severity = check.severity if check.name not in wrong_severity else Severity.SC_CRITICAL
						entries.append(self.entry(check, check.code, severity))
				key = (check.name, 'recovery')
				if (check.phase == 'recovery' and key not in self.sent
						and self.now >= check.changed_at + check.recovery_delay + 2):
					self.sent.add(key)
					if key not in omitted:
						entries.append(self.entry(check, check.recovery_code, check.recovery_severity))
				key = (check.name, 'intermediate')
				if (intermediate_recovery and check.phase == 'intermediate' and key not in self.sent
						and self.now >= check.confirmed_at + s.RECOVERY_DELAY + 2):
					self.sent.add(key)
					entries.append(self.entry(check, check.recovery_code, check.recovery_severity))
			return entries
		s._read_journal = read

	@staticmethod
	def entry(check, code, severity):
		return SimpleNamespace(param=check.program.get_id(), code=code, severity=severity)

	def snapshot(self):
		self.scenario._journal_cursor = None
		return True

	def wait(self, seconds):
		self.now += seconds
		return True

	def change(self, check, value):
		self.changes.append((check.name, value, self.now))
		check.changed_at = check.confirmed_at = self.now

	def run(self):
		with patch('scenario.base.journal_temperature.print_log'), patch('scenario.base.journal_temperature.print_error'):
			self.scenario.run()
		return self.scenario.get_checklist_results()


class TestTemperatureJournalRuns(unittest.TestCase):
	def test_moderate_success_takes_one_hour_not_two(self):
		run = TemperatureRun(ModerateScenario)
		self.assertEqual(run.run(), {'9.16': 'OK', '9.17': 'OK'})
		self.assertEqual(run.scenario.get_status(), 'OK')
		self.assertLess(run.now - 100, ModerateScenario.ONE_HOUR + 120)
		self.assertTrue(run.cleaned)
		self.assertTrue(any(cursor is not None for cursor in run.cursors))

	def test_missing_recovery_does_not_undo_underheating(self):
		run = TemperatureRun(ModerateScenario, omitted={('circuit', 'recovery')})
		self.assertEqual(run.run(), {'9.16': 'OK', '9.17': 'FAIL'})
		self.assertTrue(next(c for c in run.checks if c.name == 'dhw').recovery_ok)
		self.assertEqual(run.scenario.get_status(), 'FAIL')

	def test_missing_underheating_does_not_stop_other_consumer(self):
		run = TemperatureRun(ModerateScenario, omitted={('circuit', 'cold')})
		self.assertEqual(run.run(), {'9.16': 'FAIL', '9.17': 'FAIL'})
		self.assertTrue(next(c for c in run.checks if c.name == 'dhw').recovery_ok)

	def test_both_programs_in_same_batch_are_not_lost(self):
		run = TemperatureRun(ModerateScenario, simultaneous=True)
		self.assertEqual(run.run(), {'9.16': 'OK', '9.17': 'OK'})

	def test_early_underheating_is_failure(self):
		run = TemperatureRun(ModerateScenario, early={'circuit'})
		self.assertEqual(run.run(), {'9.16': 'FAIL', '9.17': 'FAIL'})

	def test_wrong_severity_is_failure(self):
		run = TemperatureRun(ModerateScenario, wrong_severity={'dhw'})
		self.assertEqual(run.run(), {'9.16': 'FAIL', '9.17': 'FAIL'})

	def test_severe_success_includes_intermediate_plateau(self):
		run = TemperatureRun(SevereScenario)
		self.assertEqual(run.run(), {'9.18': 'OK', '9.19': 'OK'})
		changes = [(value, when) for name, value, when in run.changes if name == 'cascade']
		self.assertEqual([value for value, when in changes], [35, 50, 60])
		self.assertGreaterEqual(changes[2][1] - changes[1][1], run.scenario.INTERMEDIATE_HOLD)

	def test_old_firmware_recovery_at_minimum_fails_only_9_19(self):
		run = TemperatureRun(SevereScenario, intermediate_recovery=True)
		self.assertEqual(run.run(), {'9.18': 'OK', '9.19': 'FAIL'})

	def test_missing_cascade_recovery_keeps_9_18_ok(self):
		run = TemperatureRun(SevereScenario, omitted={('cascade', 'recovery')})
		self.assertEqual(run.run(), {'9.18': 'OK', '9.19': 'FAIL'})

	def test_missing_room_entry_does_not_fail_cascade_recovery(self):
		run = TemperatureRun(SevereScenario, omitted={('room', 'cold')})
		self.assertEqual(run.run(), {'9.18': 'FAIL', '9.19': 'OK'})

	def test_cleanup_failure_invalidates_results(self):
		run = TemperatureRun(ModerateScenario, cleanup_error=True)
		self.assertEqual(run.run(), {'9.16': 'FAIL', '9.17': 'FAIL'})
		self.assertEqual(run.scenario.get_status(), 'FAIL')

	def test_cancellation_keeps_completed_checklist_item(self):
		run = TemperatureRun(SevereScenario)
		original_read = run.scenario._read_journal
		def read(cursor):
			if all(c.cold_ok for c in run.checks):
				raise ThreadStoppedException('cancelled')
			return original_read(cursor)
		run.scenario._read_journal = read
		with self.assertRaises(ThreadStoppedException):
			run.run()
		self.assertTrue(run.cleaned)
		self.assertEqual(run.scenario.get_checklist_results(), {'9.18': 'OK', '9.19': 'FAIL'})


class TestTemperaturePreparation(unittest.TestCase):
	def scenario(self, scenario_class=ModerateScenario):
		s = scenario_class.__new__(scenario_class)
		s._programList = make_programs(s)
		s._manualSensorsList = []
		s._virtual_outdoor = None
		return s

	def test_moderate_temperature_stays_above_minimum(self):
		s = self.scenario()
		circuit, dhw = s.make_checks()
		self.assertGreater(circuit.cold, s.CIRCUIT_MINIMUM)
		self.assertLess(circuit.cold, circuit.warm - 5)
		self.assertLess(dhw.cold, dhw.warm - s.DHW_HYSTERESIS)

	def test_settings_have_protocol_metadata(self):
		for cls in (ModerateScenario, SevereScenario):
			for _, kind, key, value in self.scenario(cls).settings():
				with self.subTest(scenario=cls.__name__, kind=kind, key=key):
					self.assertIsNotNone(get_parameter(kind, key))

	def test_all_required_programs_exist_in_presets(self):
		for cls, loader in ((ModerateScenario, moderate_preset), (SevereScenario, severe_preset)):
			programs, hosts = loader()
			types = [program.get_type() for program in programs]
			for kind in self.scenario(cls).get_required_programs().values():
				self.assertIn(kind, types)
			self.assertEqual(len({p.get_id() for p in programs}), len(programs))
			self.assertEqual(len(hosts), 1)

	def test_failed_parameter_write_is_also_restored(self):
		s = self.scenario()
		program = s._programList['circuit']
		key = snc.HeatingCircuitParameterId.PUMP_MODE
		s.settings = lambda: [(program, snc.ProgramType.HEATING_CIRCUIT, key, 2)]
		s.read_parameter = Mock(return_value=4)
		s.write_parameter = Mock(side_effect=[RuntimeError('write failed'), None])
		checks = s.make_checks()
		with self.assertRaisesRegex(RuntimeError, 'write failed'):
			with s.temperature_configuration(checks):
				self.fail('failed preparation must not enter body')
		s.write_parameter.assert_called_with(program, snc.ProgramType.HEATING_CIRCUIT, key, 4)
		for check in checks:
			check.sensor.set_manual.assert_called_with(False)
		self.assertEqual(s._manualSensorsList, [])

	def test_unknown_parameter_prevents_all_mutations(self):
		s = self.scenario()
		s.read_parameter = Mock(side_effect=RuntimeError('no read response'))
		s.write_parameter = Mock()
		s.set_sensor_value = Mock()
		with self.assertRaisesRegex(RuntimeError, 'no read response'):
			with s.temperature_configuration(s.make_checks()):
				self.fail('preparation must fail')
		s.write_parameter.assert_not_called()
		s.set_sensor_value.assert_not_called()

	def test_restoration_error_still_restores_sensors(self):
		s = self.scenario()
		program = s._programList['circuit']
		key = snc.HeatingCircuitParameterId.PUMP_MODE
		s.settings = lambda: [(program, snc.ProgramType.HEATING_CIRCUIT, key, 2)]
		s.read_parameter = Mock(return_value=4)
		s.write_parameter = Mock(side_effect=[None, RuntimeError('restore failed')])
		checks = s.make_checks()
		with self.assertRaisesRegex(RuntimeError, 'restore failed'):
			with s.temperature_configuration(checks):
				pass
		self.assertTrue(s._cleanup_failed)
		for check in checks:
			check.sensor.set_manual.assert_called_with(False)
		self.assertEqual(s._manualSensorsList, [])


class TestChecklistResults(unittest.TestCase):
	def test_default_single_result_and_two_independent_results(self):
		thread = object.__new__(ScenarioThread)
		thread._scenarioResultList = []
		thread.print_result = Mock()
		single = Scenario.__new__(Scenario)
		single._status = 'OK'
		single.get_duration = lambda: 10
		single_completion = thread.append_scenario_result(single)
		combined = ModerateScenario.__new__(ModerateScenario)
		combined._checklist_results = {'9.16': 'OK', '9.17': 'FAIL'}
		combined.get_duration = lambda: 3700
		completion = thread.append_scenario_result(combined)
		self.assertEqual(thread._scenarioResultList, [
			{'checklistId': '--', 'result': 'OK', 'duration': 10},
			{'checklistId': '9.16', 'result': 'OK', 'duration': 3700},
			{'checklistId': '9.17', 'result': 'FAIL', 'duration': 3700},
		])
		self.assertEqual(single_completion, thread._scenarioResultList[0])
		self.assertEqual(completion['checklistId'], '9.16, 9.17')
		self.assertEqual(completion['result'], 'FAIL')
		self.assertEqual(completion['checklistResults'], thread._scenarioResultList[1:])

	def test_failure_callback_preserves_success_and_notifies_only_once(self):
		thread = object.__new__(ScenarioThread)
		thread._result_callback = Mock()
		scenario = ModerateScenario.__new__(ModerateScenario)
		scenario._checklist_results = {'9.16': 'OK', '9.17': 'FAIL'}
		scenario.get_duration = lambda: 3700
		thread._report_failure(scenario, RuntimeError('cancelled'))
		thread._result_callback.assert_called_once()
		completion = thread._result_callback.call_args.args[0]
		self.assertEqual(completion['result'], 'FAIL')
		self.assertEqual([(r['checklistId'], r['result']) for r in completion['checklistResults']],
			[('9.16', 'OK'), ('9.17', 'FAIL')])


if __name__ == '__main__':
	unittest.main()
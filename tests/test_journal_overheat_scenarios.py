import unittest
from unittest.mock import Mock, patch

from scenario.list.journal.scenario_journal_9_20 import Scenario as CircuitScenario
from scenario.list.journal.scenario_journal_9_21_and_9_22 import Scenario as BoilerScenario
from scenario.scenario import ThreadStoppedException
from presets.list.journal_low_temperature import get_presets_list
import smartnet.constants as snc
from smartnet.message_log_constants import SeverityCode as Severity
from smartnet.parameter_registry import get_parameter
from tests.test_journal_temperature_scenarios import TemperatureRun, make_programs


class TestOverheatScenarios(unittest.TestCase):
	def test_success_uses_real_delays(self):
		for cls, delay in ((CircuitScenario, 120), (BoilerScenario, 300)):
			with self.subTest(scenario=cls):
				run = TemperatureRun(cls)
				self.assertEqual(run.run(), dict.fromkeys(run.scenario.get_checklist_id().split(', '), 'OK'))
				self.assertEqual(cls.OVERHEAT_DELAY, delay)
				self.assertGreaterEqual(run.now - 100, delay + cls.BASELINE_HOLD)
				self.assertTrue(run.cleaned)
				self.assertEqual(run.changes[-1][1], run.checks[0].warm)

	def test_early_missing_and_wrong_severity_fail(self):
		for cls in (CircuitScenario, BoilerScenario):
			for options in ({'early': {cls.TARGET}}, {'omitted': {(cls.TARGET, 'cold')}},
					{'wrong_severity': {cls.TARGET}}, {'cleanup_error': True}):
				with self.subTest(scenario=cls, options=options):
					run = TemperatureRun(cls, **options)
					self.assertEqual(run.run(), dict.fromkeys(run.scenario.get_checklist_id().split(', '), 'FAIL'))
					self.assertTrue(run.cleaned)

	def test_recovery_checks_boundary_before_cooling(self):
		run = TemperatureRun(BoilerScenario)
		self.assertEqual(run.run(), {'9.21': 'OK', '9.22': 'OK'})
		check = run.checks[0]
		self.assertEqual([value for _, value, _ in run.changes], [85, 75, 74])
		self.assertGreaterEqual(run.changes[2][2] - run.changes[1][2], BoilerScenario.INTERMEDIATE_HOLD)
		self.assertEqual(check.recovery_delay, 30)
		self.assertEqual(check.recovery_severity, Severity.SC_INFORMATIONAL)

	def test_missing_and_boundary_recovery_preserve_overheat_result(self):
		for options in ({'omitted': {('boiler', 'recovery')}}, {'intermediate_recovery': True}):
			with self.subTest(options=options):
				run = TemperatureRun(BoilerScenario, **options)
				self.assertEqual(run.run(), {'9.21': 'OK', '9.22': 'FAIL'})
				self.assertEqual(run.scenario._status, 'FAIL')
				self.assertTrue(run.cleaned)

	def test_invalid_recovery_time_severity_and_program_id(self):
		for fault in ('early', 'severity', 'program_id', 'transport'):
			with self.subTest(fault=fault):
				run = TemperatureRun(BoilerScenario)
				check = run.checks[0]
				original_read = run.scenario._read_journal
				def read(cursor):
					if fault == 'transport' and check.phase == 'recovery':
						return None
					if (fault == 'early' and check.phase == 'recovery'
							and run.now >= check.changed_at + check.recovery_delay - 10):
						return [run.entry(check, check.recovery_code, check.recovery_severity)]
					entries = original_read(cursor)
					for entry in entries:
						if entry.code == check.recovery_code:
							if fault == 'severity':
								entry.severity = check.severity
							elif fault == 'program_id':
								entry.param += 1
					return entries
				run.scenario._read_journal = read
				self.assertEqual(run.run(), {'9.21': 'OK', '9.22': 'FAIL'})
				self.assertTrue(run.cleaned)

	def test_cancellation_after_overheat_preserves_first_result(self):
		run = TemperatureRun(BoilerScenario)
		def wait(seconds):
			return False if run.checks[0].phase == 'intermediate' else run.wait(seconds)
		run.scenario.wait = wait
		with self.assertRaises(ThreadStoppedException):
			run.run()
		self.assertEqual(run.scenario.get_checklist_results(), {'9.21': 'OK', '9.22': 'FAIL'})
		self.assertEqual(run.scenario._status, 'FAIL')
		self.assertTrue(run.cleaned)

	def test_cancellation_restores_and_does_not_succeed(self):
		run = TemperatureRun(CircuitScenario)
		run.scenario.wait = Mock(return_value=False)
		with self.assertRaises(ThreadStoppedException):
			run.run()
		self.assertTrue(run.cleaned)
		self.assertEqual(run.scenario._status, 'FAIL')

	def scenario(self, cls):
		s = cls.__new__(cls)
		s._status = 'FAIL'
		s._programList = make_programs(s)
		s._manualSensorsList = []
		s._virtual_outdoor = None
		return s

	def test_protocol_settings_and_preset(self):
		programs, _ = get_presets_list()
		for cls in (CircuitScenario, BoilerScenario):
			s = self.scenario(cls)
			for _, kind, key, _ in s.settings():
				self.assertIsNotNone(get_parameter(kind, key))
			for kind in s.get_required_programs().values():
				self.assertIn(kind, [program.get_type() for program in programs])
			check = s.make_checks()[0]
			if cls is CircuitScenario:
				self.assertGreater(check.cold, s.CIRCUIT_MAXIMUM + 5)
			else:
				self.assertEqual(check.cold, s.BOILER_COOLING_TEMPERATURE + 5)
				self.assertLess(s.BOILER_MAXIMUM, s.BOILER_COOLING_TEMPERATURE)

	def test_lost_temperature_and_circulation_fail(self):
		for cls in (CircuitScenario, BoilerScenario):
			s = self.scenario(cls)
			s.input_is = Mock(return_value=False)
			with self.assertRaises(RuntimeError):
				s.validate_operating_state(s.make_checks())
		s = self.scenario(CircuitScenario)
		s.input_is = Mock(return_value=True)
		for value in (None, s.RELAY_OFF):
			s._programList['circuit'].get_output_channel('pump').get_value.return_value = value
			with self.assertRaisesRegex(RuntimeError, 'циркуляция'):
				s.validate_operating_state(s.make_checks())

	def test_failed_write_restores_parameters_and_inputs(self):
		for cls in (CircuitScenario, BoilerScenario):
			s = self.scenario(cls)
			program = s._programList['circuit']
			key = snc.HeatingCircuitParameterId.PUMP_MODE
			s.settings = lambda: [(program, snc.ProgramType.HEATING_CIRCUIT, key, 2)]
			s.read_parameter = Mock(return_value=4)
			s.write_parameter = Mock(side_effect=[RuntimeError('write failed'), None])
			with self.assertRaisesRegex(RuntimeError, 'write failed'):
				with s.temperature_configuration(s.make_checks()):
					self.fail('failed write must prevent the test')
			s.write_parameter.assert_called_with(program, snc.ProgramType.HEATING_CIRCUIT, key, 4)
			for name in (s.TARGET, 'boiler'):
				s._programList[name].get_input_channel('temperature').set_manual.assert_called_with(False)
			self.assertEqual(s._manualSensorsList, [])


if __name__ == '__main__':
	with patch('scenario.base.journal_overheat.print_log'):
		unittest.main()
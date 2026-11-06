from contextlib import contextmanager
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scenario.list.journal.scenario_journal_9_33 import Scenario as PowerScenario
from scenario.list.journal.scenario_journal_9_34 import Scenario as TemperatureScenario
from scenario.scenario import ThreadStoppedException
from presets.list.journal_boiler_faults import get_presets_list
import smartnet.constants as snc
from smartnet.message_log_constants import MessageLogCode as Code, SeverityCode as Severity
from smartnet.parameter_registry import get_parameter


def make_scenario(cls=PowerScenario):
	s = cls.__new__(cls)
	s._manualSensorsList = []
	s._virtual_outdoor = None
	s._programList = {}
	for index, (name, kind) in enumerate(s.get_required_programs().items(), 101):
		program = Mock()
		program.get_id.return_value = index
		program.get_type.return_value = kind
		channels = {}
		def channel(name, channels=channels):
			if name not in channels:
				channels[name] = Mock()
				channels[name].get_value.return_value = 22
				channels[name].is_mapped.return_value = True
				channels[name].isManual.return_value = False
				channels[name].isShort.return_value = False
				channels[name].isOpen.return_value = False
			return channels[name]
		program.get_input_channel.side_effect = channel
		s._programList[name] = program
	return s


class FaultRun:
	"""Synthetic transport observations, not firmware or hardware validation."""
	def __init__(self, cls=PowerScenario, offset=0, code=None, severity=Severity.SC_WARNING,
			program_id=102, missing=False, cleanup_error=False):
		self.now = 100.0
		self.cleaned = False
		self.sent = False
		self.scenario = s = make_scenario(cls)
		s.clock = lambda: self.now
		s.wait = self.wait
		s.wait_event = lambda condition, timeout: condition()
		s.inputs_are = Mock(return_value=True)
		s.operating_state_is_valid = Mock(return_value=True)
		s.read_parameter = Mock(return_value=0)
		s.set_sensor_value = Mock()
		s.snapshot_journal = self.snapshot
		@contextmanager
		def configuration():
			s._flow_sensor = Mock()
			s._return_sensor = Mock()
			try:
				yield
			finally:
				self.cleaned = True
				if cleanup_error:
					raise RuntimeError('restoration failed')
		s.fault_configuration = configuration
		def read(cursor):
			if not missing and not self.sent and self.now >= self.started + s.ALARM_DELAY + offset:
				self.sent = True
				return [SimpleNamespace(code=s.expected_code() if code is None else code,
					severity=severity, param=program_id)]
			return []
		s._read_journal = read

	def snapshot(self):
		self.scenario._journal_cursor = None
		self.started = self.now
		return True

	def wait(self, seconds):
		self.now += seconds
		return True

	def run(self):
		with patch('scenario.base.journal_boiler_faults.print_log'), patch('scenario.base.journal_boiler_faults.print_error'):
			self.scenario.run()
		return self.scenario._status


class TestBoilerJournalRuns(unittest.TestCase):
	def test_both_faults_pass_after_fifty_minutes(self):
		for cls in (PowerScenario, TemperatureScenario):
			with self.subTest(scenario=cls):
				run = FaultRun(cls)
				self.assertEqual(run.run(), 'OK')
				self.assertGreaterEqual(run.now - run.started, 50 * 60)
				self.assertTrue(run.cleaned)

	def test_early_entry_fails(self):
		self.assertEqual(FaultRun(offset=-30).run(), 'FAIL')

	def test_wrong_code_fails(self):
		self.assertEqual(FaultRun(code=Code.MLC_BOILER_TEMPERATURE_IS_LOW).run(), 'FAIL')

	def test_wrong_severity_fails(self):
		self.assertEqual(FaultRun(severity=Severity.SC_CRITICAL).run(), 'FAIL')

	def test_wrong_program_is_not_accepted(self):
		self.assertEqual(FaultRun(program_id=101).run(), 'FAIL')

	def test_missing_entry_times_out(self):
		run = FaultRun(missing=True)
		self.assertEqual(run.run(), 'FAIL')
		self.assertTrue(run.cleaned)

	def test_incomplete_journal_fails(self):
		run = FaultRun()
		run.scenario._read_journal = lambda cursor: None
		self.assertEqual(run.run(), 'FAIL')

	def test_lost_burner_or_demand_fails(self):
		run = FaultRun()
		run.scenario.operating_state_is_valid.side_effect = [True, True, False]
		self.assertEqual(run.run(), 'FAIL')

	def test_temperature_drift_fails(self):
		run = FaultRun()
		run.scenario.inputs_are.side_effect = [True, True, True, False]
		self.assertEqual(run.run(), 'FAIL')

	def test_cleanup_failure_cannot_pass(self):
		self.assertEqual(FaultRun(cleanup_error=True).run(), 'FAIL')

	def test_cancellation_restores_configuration(self):
		run = FaultRun()
		run.scenario.wait = lambda seconds: False
		with self.assertRaises(ThreadStoppedException):
			run.run()
		self.assertTrue(run.cleaned)
		self.assertEqual(run.scenario._status, 'FAIL')

	def test_alarm_may_switch_burner_off(self):
		run = FaultRun()
		run.scenario.operating_state_is_valid.side_effect = lambda: not run.sent
		self.assertEqual(run.run(), 'OK')


class TestBoilerJournalConfiguration(unittest.TestCase):
	def test_fault_conditions_are_isolated(self):
		for cls in (PowerScenario, TemperatureScenario):
			s = make_scenario(cls)
			flow, backward = s.fault_temperatures()
			low_power = flow < backward + s.HYSTERESIS and flow < s.SETPOINT - s.HYSTERESIS
			self.assertEqual(low_power, s.LOW_POWER)
			self.assertEqual(flow < s.WARMUP_TEMPERATURE, not s.LOW_POWER)

	def test_preset_and_protocol_metadata(self):
		programs, hosts = get_presets_list()
		s = make_scenario()
		self.assertEqual(set(s.get_required_programs().values()), {p.get_type() for p in programs})
		self.assertEqual(len(hosts), 1)
		for _, kind, key, value in s.settings():
			self.assertIsNotNone(get_parameter(kind, key), (kind, key))

	def test_failed_write_is_restored_and_all_inputs_released(self):
		s = make_scenario()
		program = s._programList['boiler']
		setting = (program, snc.ProgramType.BOILER, snc.BoilerParameterId.WARMUP_TEMPERATURE)
		s.settings = lambda: [(*setting, 30)]
		s.read_parameter = Mock(return_value=45)
		s.write_parameter = Mock(side_effect=[RuntimeError('write failed'), None])
		with self.assertRaisesRegex(RuntimeError, 'write failed'):
			with s.fault_configuration():
				self.fail('preparation must fail')
		s.write_parameter.assert_called_with(*setting, 45)
		for name, channel in [('boiler', 'temperature'), ('boiler', 'backwardTemperature'), ('circuit', 'temperature')]:
			s._programList[name].get_input_channel(channel).set_manual.assert_called_with(False)
		self.assertEqual(s._manualSensorsList, [])

	def test_failed_read_prevents_mutations(self):
		s = make_scenario()
		s.read_parameter = Mock(side_effect=RuntimeError('read failed'))
		s.set_sensor_value = Mock()
		s.write_parameter = Mock()
		with self.assertRaisesRegex(RuntimeError, 'read failed'):
			with s.fault_configuration():
				self.fail('preparation must fail')
		s.set_sensor_value.assert_not_called()
		s.write_parameter.assert_not_called()

	def test_missing_mapping_fails_before_writes(self):
		s = make_scenario()
		s._programList['boiler'].get_input_channel('backwardTemperature').is_mapped.return_value = False
		s.write_parameter = Mock()
		with self.assertRaisesRegex(RuntimeError, 'датчик'):
			with s.fault_configuration():
				self.fail('preparation must fail')
		s.write_parameter.assert_not_called()


if __name__ == '__main__':
	unittest.main()
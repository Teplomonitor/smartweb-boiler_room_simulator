import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scenario.base.journal import JournalScenarioMixin, ScenarioJournalReader
from scenario.base.journal_collision import JournalCollisionScenario
from scenario.list.journal.scenario_journal_9_1 import Scenario as CollisionScenario
from scenario.list.journal.scenario_journal_9_2 import Scenario as CollisionResolvedScenario
from scenario.list.journal.scenario_journal_9_3 import Scenario as OutdoorConflictScenario
from scenario.list.journal.scenario_journal_9_4 import Scenario as DisinfectionStartScenario
from scenario.list.journal.scenario_journal_9_5 import Scenario as DisinfectionEndScenario
from scenario.list.journal.scenario_journal_9_6 import Scenario as WarmupStartScenario
from scenario.list.journal.scenario_journal_9_7 import Scenario as WarmupEndScenario
from scenario.list.journal.scenario_journal_9_9 import Scenario as AlarmEndedScenario
from scenario.list.journal.scenario_journal_9_10 import Scenario as AlarmResetScenario
from scenario.list.journal.scenario_journal_9_11 import Scenario as LowPressureScenario
from scenario.list.journal.scenario_journal_9_12 import Scenario as PressureRestoredScenario
from scenario.list.journal.scenario_journal_9_13 import Scenario as AutoFillScenario
from scenario.list.journal.scenario_journal_9_28 import Scenario as PoolLevelScenario
from scenario.list.journal.scenario_journal_9_29 import Scenario as PoolFlowAlarmScenario
from scenario.list.journal.scenario_journal_9_30 import Scenario as PoolFlowRestoredScenario
from scenario.list.journal.scenario_journal_9_32 import Scenario as BoilerErrorScenario
from presets.list.boiler_journal_error import get_presets_list
from presets.list.journal_outdoor import get_presets_list as get_outdoor_preset
from presets.list.journal_pool_flow import get_presets_list as get_pool_flow_preset
from presets.list.alarm import get_presets_list as get_alarm_preset
from programs.alarm import Alarm
import smartnet.constants as snc
from smartnet.parameter_registry import get_parameter
from smartnet.message_log_constants import MessageLogCode, SeverityCode
from smartnet.message import Message


class TestJournalCursor(unittest.TestCase):
	def setUp(self):
		self.scenario = JournalScenarioMixin()
		self.scenario._controllerHost = Mock()
		self.scenario._controllerHost.get_controller_id.return_value = 123
		self.scenario.wait = Mock()

	def test_snapshot_then_match_only_new_entry(self):
		old = SimpleNamespace(code=16, severity=2, param=101, param_ex=bytes(8))
		other = SimpleNamespace(code=53, severity=5, param=102, param_ex=bytes(8))
		new = SimpleNamespace(code=16, severity=2, param=101, param_ex=bytes(8))
		seen_cursors = []

		def read(cursor):
			seen_cursors.append(cursor)
			return [[old], [other], [new]][len(seen_cursors) - 1]

		self.scenario._read_journal = Mock(side_effect=read)
		self.assertTrue(self.scenario.snapshot_journal())
		self.assertTrue(self.scenario.wait_journal_entry(16, 2, 101, timeout=30))
		self.assertEqual(seen_cursors, [None, old, other])
		self.assertIs(self.scenario._journal_cursor, new)

	def test_incomplete_read_is_not_treated_as_empty_journal(self):
		with patch('scenario.base.journal.ScenarioJournalReader') as reader, \
				patch('scenario.base.journal.CanListener.unsubscribe') as unsubscribe:
			reader.return_value.read_entries.return_value = []
			reader.return_value.status_received = False
			self.assertFalse(self.scenario.snapshot_journal())
			reader.assert_called_once_with(controller_id=123, timeout=3)
			unsubscribe.assert_called_once_with(reader.return_value)

	def test_status_is_recognized_without_decoding_legacy_bytes(self):
		with patch('scenario.base.journal.CanListener.subscribe'), \
				patch('scenario.base.journal.CanListener.unsubscribe'):
			reader = ScenarioJournalReader(controller_id=123, timeout=0)
			reader._start_capture(123)
			try:
				other = Message(reader.PROGRAM_TYPE, 124, reader.FUNCTION_ID,
					reader.RESPONSE_FLAG, bytes(8))
				reader.on_can_message_received(other)
				self.assertFalse(reader.status_received)
				status = Message(reader.PROGRAM_TYPE, 123, reader.FUNCTION_ID,
					reader.RESPONSE_FLAG, bytes(8))
				reader.on_can_message_received(status)
				self.assertTrue(reader.status_received)
			finally:
				reader._stop_capture()


class TestJournalFillingLoopScenarios(unittest.TestCase):
	def check_scenario(self, scenario_class, code, severity):
		scenario = scenario_class.__new__(scenario_class)
		scenario._filling_loop = Mock()
		scenario._filling_loop.get_id.return_value = 101
		scenario.prepare_journal_test = Mock(return_value=True)
		scenario.snapshot_journal = Mock(return_value=True)
		scenario.set_low_pressure = Mock(return_value=True)
		scenario.set_normal_pressure = Mock(return_value=True)
		scenario.write_parameter = Mock(return_value=True)
		scenario.wait_event = Mock(return_value=True)
		scenario.wait_journal_entry = Mock(return_value=True)
		scenario.finish_journal_test = Mock()
		scenario.run()
		self.assertEqual(scenario._status, 'OK')
		scenario.wait_journal_entry.assert_called_once_with(
			code, severity, 101, scenario.EVENT_TIMEOUT)
		scenario.finish_journal_test.assert_called_once()
		return scenario

	def test_low_pressure(self):
		scenario = self.check_scenario(LowPressureScenario,
			MessageLogCode.MLC_LOW_PRESSURE_ALARM_STARTED, SeverityCode.SC_CRITICAL)
		scenario.prepare_journal_test.assert_called_once_with(short_alarm=True)

	def test_pressure_restored(self):
		scenario = self.check_scenario(PressureRestoredScenario,
			MessageLogCode.MLC_LOW_PRESSURE_ALARM_ENDED, SeverityCode.SC_NOTICE)
		scenario.set_normal_pressure.assert_called_once()

	def test_auto_fill(self):
		scenario = self.check_scenario(AutoFillScenario,
			MessageLogCode.MLC_FL_AUTO_FILL_STARTED, SeverityCode.SC_NOTICE)
		scenario.write_parameter.assert_called_once_with('autoFill', 1)

	def test_cleanup_after_failed_read(self):
		scenario = LowPressureScenario.__new__(LowPressureScenario)
		scenario.prepare_journal_test = Mock(return_value=True)
		scenario.snapshot_journal = Mock(return_value=False)
		scenario.finish_journal_test = Mock()
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		scenario.finish_journal_test.assert_called_once()


class TestAdditionalJournalScenarios(unittest.TestCase):
	def test_boiler_error_input_is_bound_to_distinct_channel(self):
		programs, _ = get_presets_list()
		boiler = next(program for program in programs if program.get_type() == snc.ProgramType.BOILER)
		self.assertIsNotNone(boiler.getInput(3))
		self.assertNotEqual(boiler.getInput(0), boiler.getInput(3))

	def test_boiler_alarm_entry_and_input_cleanup(self):
		scenario = BoilerErrorScenario.__new__(BoilerErrorScenario)
		sensor = Mock()
		sensor.is_mapped.return_value = True
		boiler = Mock()
		boiler.get_id.return_value = 102
		boiler.get_input_channel.return_value = sensor
		scenario._programList = {'boiler': boiler}
		scenario.set_sensor_value = Mock()
		scenario.wait = Mock()
		scenario.snapshot_journal = Mock(return_value=True)
		scenario.wait_journal_entry = Mock(return_value=True)
		scenario.run()
		scenario.wait_journal_entry.assert_called_once_with(
			MessageLogCode.MLC_BOILER_ERROR, SeverityCode.SC_WARNING, 102, scenario.ALARM_TIMEOUT)
		self.assertEqual(scenario._status, 'OK')
		self.assertEqual(scenario.set_sensor_value.call_args.args, (sensor, 'open'))
		sensor.set_manual.assert_called_once_with(False)

	def test_pool_alarm_entry_and_parameter_cleanup(self):
		scenario = PoolLevelScenario.__new__(PoolLevelScenario)
		sensor = Mock()
		sensor.is_mapped.return_value = True
		pool = Mock()
		pool.get_id.return_value = 101
		pool.get_input_channel.return_value = sensor
		pool.read_parameter_value.return_value = 1200
		pool.write_parameter_value.return_value = 60
		pool.resetWaterLevelAlarm.return_value = 0
		scenario._pool = pool
		scenario.set_sensor_value = Mock()
		scenario.wait_event = Mock(return_value=True)
		scenario.snapshot_journal = Mock(return_value=True)
		scenario.wait_journal_entry = Mock(return_value=True)
		scenario.run()
		scenario.wait_journal_entry.assert_called_once_with(
			MessageLogCode.MLC_LOW_POOL_WATER_LEVEL, SeverityCode.SC_CRITICAL,
			101, scenario.FILLING_DURATION + scenario.ALARM_TIMEOUT_MARGIN + scenario.JOURNAL_TIMEOUT)
		self.assertEqual(scenario._status, 'OK')
		pool.write_parameter_value.assert_any_call('fillingDuration', 1200)
		sensor.set_manual.assert_called_once_with(False)

	def test_pool_cleanup_after_journal_failure(self):
		scenario = PoolLevelScenario.__new__(PoolLevelScenario)
		sensor = Mock()
		sensor.is_mapped.return_value = True
		pool = Mock()
		pool.get_input_channel.return_value = sensor
		pool.read_parameter_value.return_value = 1200
		pool.write_parameter_value.return_value = 60
		pool.resetWaterLevelAlarm.return_value = 0
		scenario._pool = pool
		scenario.set_sensor_value = Mock()
		scenario.wait_event = Mock(return_value=True)
		scenario.snapshot_journal = Mock(return_value=False)
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		pool.write_parameter_value.assert_any_call('fillingDuration', 1200)
		sensor.set_manual.assert_called_once_with(False)


class TestSingleControllerJournalConflicts(unittest.TestCase):
	def collision_scenario(self, scenario_class, results):
		scenario = scenario_class.__new__(scenario_class)
		boiler = Mock()
		boiler.get_id.return_value = 102
		scenario._programList = {'boiler': boiler}
		scenario._controllerHost = Mock()
		scenario._controllerHost.get_controller_id.return_value = 123
		scenario.wait = Mock()
		scenario.snapshot_journal = Mock(return_value=True)
		scenario.wait_journal_entry = Mock(side_effect=results)
		emitter = Mock()
		scenario.make_collision_emitter = Mock(return_value=emitter)
		scenario.run()
		emitter.start.assert_called_once()
		emitter.stop.assert_called_once()
		return scenario

	def test_9_1_reports_collision_cid_pid(self):
		scenario = self.collision_scenario(CollisionScenario, [True])
		self.assertEqual(scenario._status, 'OK')
		scenario.wait_journal_entry.assert_called_once_with(
			MessageLogCode.MLC_CONTROLLER_ERROR, SeverityCode.SC_ALERT, 0,
			scenario.JOURNAL_TIMEOUT, param_ex=[123, 102])

	def test_9_2_waits_for_resolution_after_stopping_emitter(self):
		scenario = self.collision_scenario(CollisionResolvedScenario, [True, True])
		self.assertEqual(scenario._status, 'OK')
		self.assertEqual(scenario.snapshot_journal.call_count, 2)
		self.assertEqual(scenario.wait_journal_entry.call_args.args,
			(MessageLogCode.MLC_CONTROLLER_ERROR_IS_OK, SeverityCode.SC_INFORMATIONAL,
			0, scenario.RESOLUTION_TIMEOUT))
		self.assertEqual(scenario.wait_journal_entry.call_args.kwargs, {'param_ex': [102]})

	def test_collision_emitter_uses_two_distinct_markers(self):
		scenario = JournalCollisionScenario.__new__(JournalCollisionScenario)
		scenario._controllerHost = Mock()
		scenario._controllerHost.get_controller_id.return_value = 123
		boiler = Mock()
		boiler.get_id.return_value = 102
		scenario._programList = {'boiler': boiler}
		messages = scenario.make_collision_emitter()._messages
		self.assertEqual([msg.get_data()[0] for msg in messages], [1, 2])
		for msg in messages:
			self.assertEqual(msg.get_data()[1:], [123, snc.ProgramType.BOILER])
			self.assertEqual(msg.getProgramId(), 102)
			self.assertEqual(msg.getFunctionId(), snc.ProgramFunction['I_AM_PROGRAM'])

	def test_9_3_second_sensor_response_and_cleanup(self):
		programs, _ = get_outdoor_preset()
		self.assertEqual(len(programs), 1)
		scenario = OutdoorConflictScenario.__new__(OutdoorConflictScenario)
		outdoor = Mock()
		outdoor.get_id.return_value = 101
		scenario._programList = {'outdoor': outdoor}
		scenario.snapshot_journal = Mock(return_value=True)
		scenario.wait_journal_entry = Mock(return_value=True)
		with patch('scenario.list.journal.scenario_journal_9_3.JournalCanEmitter') as emitter:
			scenario.run()
			response = emitter.call_args.args[0][0]
			emitter.return_value.stop.assert_called_once()
		self.assertEqual(response.getProgramId(), 102)
		self.assertEqual(response.getFunctionId(), snc.OutdoorSensorFunction.GET_TEMPERATURE)
		self.assertEqual(scenario._status, 'OK')
		scenario.wait_journal_entry.assert_called_once_with(
			MessageLogCode.MLC_MORE_THEN_ONE_OUTDOOR_SENSOR,
			SeverityCode.SC_ERROR, 0, scenario.JOURNAL_TIMEOUT)


class TestNewJournalScenarios(unittest.TestCase):
	def test_pool_flow_preset_and_journal_transitions(self):
		programs, _ = get_pool_flow_preset()
		pool_preset = next(program for program in programs if program.get_type() == snc.ProgramType.POOL)
		self.assertTrue(pool_preset.getInput(3).is_mapped())
		for scenario_class, codes in (
			(PoolFlowAlarmScenario, [MessageLogCode.MLC_CIRCULATION_ERROR]),
			(PoolFlowRestoredScenario, [MessageLogCode.MLC_CIRCULATION_ERROR,
				MessageLogCode.MLC_CIRCULATION_NO_ERROR]),
		):
			with self.subTest(scenario=scenario_class.__name__, codes=codes):
				scenario = scenario_class.__new__(scenario_class)
				scenario._pool = Mock()
				scenario._pool.get_id.return_value = 101
				scenario._flow_sensor = Mock()
				scenario.prepare_pool_flow = Mock(return_value=True)
				scenario.finish_pool_flow = Mock()
				scenario.snapshot_journal = Mock(return_value=True)
				scenario.set_sensor_value = Mock()
				scenario.wait_event = Mock(return_value=True)
				scenario.wait_journal_entry = Mock(return_value=True)
				scenario.run()
				self.assertEqual(scenario._status, 'OK')
				self.assertEqual([call.args[0] for call in scenario.wait_journal_entry.call_args_list], codes)
				scenario.finish_pool_flow.assert_called_once()

	def test_pool_flow_prepare_and_restore_parameters(self):
		scenario = PoolFlowAlarmScenario.__new__(PoolFlowAlarmScenario)
		pool = Mock()
		pool.read_parameter_value.side_effect = [2, 1]
		pool.write_parameter_value.return_value = 0
		flow, level = Mock(), Mock()
		flow.is_mapped.return_value = True
		level.is_mapped.return_value = True
		pool.get_input_channel.side_effect = lambda name: {'flow': flow, 'waterLevel': level}[name]
		scenario._pool = pool
		scenario.set_sensor_value = Mock()
		scenario.wait_event = Mock(return_value=True)
		self.assertTrue(scenario.prepare_pool_flow())
		scenario.finish_pool_flow()
		pool.write_parameter_value.assert_any_call('workMode', 2)
		pool.write_parameter_value.assert_any_call('circulationPumpWorkMode', 1)
		flow.set_manual.assert_called_once_with(False)
		level.set_manual.assert_called_once_with(False)

	def test_warmup_journal_transitions_and_cleanup(self):
		for scenario_class, codes in (
			(WarmupStartScenario, [MessageLogCode.MLC_BOILER_WARM_UP_STARTED]),
			(WarmupEndScenario, [MessageLogCode.MLC_BOILER_WARM_UP_STARTED,
				MessageLogCode.MLC_BOILER_WARM_UP_ENDED]),
		):
			with self.subTest(codes=codes):
				scenario = scenario_class.__new__(scenario_class)
				scenario._boiler = Mock()
				scenario._boiler.get_id.return_value = 102
				scenario._boiler_sensor = Mock()
				scenario.prepare_boiler_warmup = Mock(return_value=True)
				scenario.finish_boiler_warmup = Mock()
				scenario.snapshot_journal = Mock(return_value=True)
				scenario.cold_temperature = Mock(return_value=30)
				scenario.hot_temperature = Mock(return_value=50)
				scenario.set_sensor_value = Mock()
				scenario.wait_journal_entry = Mock(return_value=True)
				scenario.run()
				self.assertEqual(scenario._status, 'OK')
				self.assertEqual([call.args[0] for call in scenario.wait_journal_entry.call_args_list], codes)
				scenario.finish_boiler_warmup.assert_called_once()

	def test_disinfection_journal_transitions_and_cleanup(self):
		for scenario_class, codes in (
			(DisinfectionStartScenario, [MessageLogCode.MLC_ANTILEGION_PROTECTION_STARTED]),
			(DisinfectionEndScenario, [MessageLogCode.MLC_ANTILEGION_PROTECTION_STARTED,
				MessageLogCode.MLC_ANTILEGION_PROTECTION_ENDED]),
		):
			with self.subTest(codes=codes):
				scenario = scenario_class.__new__(scenario_class)
				scenario.prepare_disinfection = Mock(return_value=True)
				scenario.finish_disinfection = Mock()
				scenario.snapshot_journal = Mock(return_value=True)
				scenario.wait_journal_entry = Mock(return_value=True)
				scenario.run()
				self.assertEqual(scenario._status, 'OK')
				self.assertEqual([call.args[0] for call in scenario.wait_journal_entry.call_args_list], codes)
				scenario.finish_disinfection.assert_called_once()

	def test_disinfection_restores_elapsed_real_time(self):
		scenario = DisinfectionStartScenario.__new__(DisinfectionStartScenario)
		scenario._controllerHost = Mock()
		scenario._controllerHost.read_date.return_value = (28, 2, 10, 2026)
		scenario._controllerHost.read_time.return_value = (12, 0, 0, 0)
		scenario._programList = {'dhw': Mock()}
		scenario._write_antilegion = Mock(return_value=True)
		scenario.snapshot_journal = Mock(return_value=True)
		scenario.wait = Mock()
		with patch('scenario.base.journal_dhw_disinfection.sr.RemoteControlParameter') as parameter, \
				patch('scenario.base.journal_dhw_disinfection.time.monotonic', side_effect=[100, 3760]):
			parameter.return_value.read.return_value = True
			parameter.return_value.get_value.return_value = 0
			self.assertTrue(scenario.prepare_disinfection())
			scenario.finish_disinfection()
		scenario._controllerHost.write_date.assert_any_call((25, 6, 10, 2026))
		scenario._controllerHost.write_date.assert_any_call((28, 2, 10, 2026))
		scenario._controllerHost.write_time.assert_any_call((13, 1, 0, 0))
		self.assertEqual(scenario._write_antilegion.call_args_list[-1].args, (0,))

	def test_warmup_failure_restores_sensors_and_dhw(self):
		scenario = WarmupStartScenario.__new__(WarmupStartScenario)
		scenario._boiler = Mock()
		scenario._boiler.get_id.return_value = 102
		scenario._boiler_sensor = Mock()
		scenario.prepare_boiler_warmup = Mock(return_value=True)
		scenario.snapshot_journal = Mock(return_value=True)
		scenario.cold_temperature = Mock(return_value=30)
		scenario.set_sensor_value = Mock()
		scenario.wait_journal_entry = Mock(return_value=False)
		scenario._initial_sensors = [(scenario._boiler_sensor, 40)]
		scenario._initial_parameters = [('workMode', 2)]
		scenario._dhw = Mock()
		scenario._dhw.write_parameter_value.return_value = 0
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		scenario._boiler_sensor.set_manual.assert_called_once_with(False)
		scenario._dhw.write_parameter_value.assert_called_once_with('workMode', 2)

	def test_disinfection_failure_still_restores_clock(self):
		scenario = DisinfectionStartScenario.__new__(DisinfectionStartScenario)
		scenario._controllerHost = Mock()
		scenario._controllerHost.read_date.return_value = (28, 2, 10, 2026)
		scenario._controllerHost.read_time.return_value = (12, 0, 0, 0)
		scenario._programList = {'dhw': Mock()}
		scenario._write_antilegion = Mock(return_value=True)
		scenario.snapshot_journal = Mock(return_value=True)
		scenario.wait_journal_entry = Mock(return_value=False)
		scenario.wait = Mock()
		with patch('scenario.base.journal_dhw_disinfection.sr.RemoteControlParameter') as parameter, \
				patch('scenario.base.journal_dhw_disinfection.time.monotonic', side_effect=[100, 160]):
			parameter.return_value.read.return_value = True
			parameter.return_value.get_value.return_value = 1
			scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		scenario._controllerHost.write_time.assert_any_call((12, 1, 0, 0))
		self.assertEqual(scenario._write_antilegion.call_args_list[-1].args, (1,))


class TestAlarmJournalScenarios(unittest.TestCase):
	def make_scenario(self, scenario_class):
		scenario = scenario_class.__new__(scenario_class)
		sensor = Mock()
		sensor.is_mapped.return_value = True
		sensor.isShort.return_value = False
		sensor.isOpen.return_value = True
		alarm = Mock()
		alarm.get_id.return_value = 101
		alarm.get_alarm_input.return_value = sensor
		alarm.read_parameter_value.side_effect = [0, 5, 1, 0]
		alarm.write_parameter.return_value = True
		alarm.reset_alarm_input.return_value = True
		scenario._programList = {'alarm': alarm}
		scenario.set_sensor_value = Mock()
		scenario.wait = Mock()
		scenario.simple_wait = Mock()
		scenario.snapshot_journal = Mock(return_value=True)
		scenario.wait_journal_entry = Mock(return_value=True)
		return scenario, alarm, sensor

	def test_alarm_preset_and_indexed_protocol(self):
		programs, _ = get_alarm_preset()
		alarm = Alarm(programs[0])
		self.addCleanup(alarm.clear)
		self.assertEqual(alarm.get_type(), snc.ProgramType.ALARM)
		self.assertTrue(alarm.get_alarm_input(0).is_mapped())
		for name, parameter_id, parameter_type in (
			('input_type', snc.AlarmParameterId.INPUT_TYPE, 'UINT8_T'),
			('input_control', snc.AlarmParameterId.INPUT_CONTROL, 'UINT8_T'),
			('alarm_delay', snc.AlarmParameterId.ALARM_DELAY, 'TIME_MS'),
			('auto_reset', snc.AlarmParameterId.AUTO_RESET, 'UINT8_T'),
			('enable_log', snc.AlarmParameterId.ENABLE_LOG, 'UINT8_T'),
		):
			with self.subTest(name=name):
				self.assertEqual(alarm.get_parameter_code(name), (snc.ProgramType.ALARM, parameter_id))
				definition = get_parameter(snc.ProgramType.ALARM, parameter_id)
				self.assertEqual((definition.type, definition.array_size), (parameter_type, 8))
		with patch.object(alarm, 'write_parameter', return_value=True) as write:
			self.assertTrue(alarm.reset_alarm_input(0))
			write.assert_called_once_with('input_control', 1, index=0)

	def test_9_9_waits_for_alarm_then_ended_message(self):
		scenario, alarm, sensor = self.make_scenario(AlarmEndedScenario)
		scenario.run()
		self.assertEqual(scenario._status, 'OK')
		self.assertEqual(scenario.snapshot_journal.call_count, 2)
		self.assertEqual(scenario.wait_journal_entry.call_args_list[0].args[:3],
			(MessageLogCode.MLC_ALARM_STARTED, SeverityCode.SC_EMERGENCY, 101))
		scenario.wait_journal_entry.assert_any_call(
			MessageLogCode.MLC_ALARM_ENDED, SeverityCode.SC_WARNING,
			101, scenario.ALARM_TIMEOUT, param_ex=[0])
		alarm.write_parameter.assert_any_call('auto_reset', 1, index=0)
		self.assertEqual(alarm.write_parameter.call_args_list[-1].args, ('enable_log', 0))
		alarm.reset_alarm_input.assert_not_called()
		sensor.set_manual.assert_called_once_with(False)

	def test_9_10_resets_only_individual_input_after_condition_clears(self):
		scenario, alarm, sensor = self.make_scenario(AlarmResetScenario)
		events = []
		scenario.set_sensor_value.side_effect = lambda _, value: events.append(value)
		alarm.reset_alarm_input.side_effect = lambda index: events.append('reset') or True
		scenario.run()
		self.assertEqual(scenario._status, 'OK')
		self.assertEqual(events[:5], ['open', 'reset', 'short', 'open', 'reset'])
		self.assertEqual(alarm.reset_alarm_input.call_count, 2)  # initial cleanup and tested reset
		scenario.wait_journal_entry.assert_any_call(
			MessageLogCode.MLC_ALARM_RESET, SeverityCode.SC_NOTICE,
			101, scenario.ALARM_TIMEOUT, param_ex=[0])
		alarm.write_parameter.assert_any_call('auto_reset', 0, index=0)
		sensor.set_manual.assert_called_once_with(False)

	def test_preexisting_short_input_is_not_modified(self):
		scenario, alarm, sensor = self.make_scenario(AlarmResetScenario)
		sensor.isShort.return_value = True
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		scenario.set_sensor_value.assert_not_called()
		alarm.write_parameter.assert_not_called()
		alarm.reset_alarm_input.assert_not_called()

	def test_parameter_read_failure_does_not_change_alarm(self):
		scenario, alarm, sensor = self.make_scenario(AlarmResetScenario)
		alarm.read_parameter_value.side_effect = [0, None]
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		scenario.set_sensor_value.assert_not_called()
		alarm.write_parameter.assert_not_called()
		alarm.reset_alarm_input.assert_not_called()
		sensor.set_manual.assert_not_called()

	def test_failure_restores_input_and_original_parameters(self):
		scenario, alarm, sensor = self.make_scenario(AlarmResetScenario)
		scenario.wait_journal_entry.return_value = False
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(scenario.snapshot_journal.call_count, 1)
		for name, value in (('input_type', 0), ('alarm_delay', 5), ('auto_reset', 1), ('enable_log', 0)):
			alarm.write_parameter.assert_any_call(name, value, index=0)
		self.assertEqual(scenario.set_sensor_value.call_args.args, (sensor, 'open'))
		sensor.set_manual.assert_called_once_with(False)


if __name__ == '__main__':
	unittest.main()
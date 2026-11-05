import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scenario.base.journal_controller import ControllerPresenceCollector, JournalControllerScenario
from scenario.list.journal.scenario_journal_9_14 import Scenario
from scenario.scenario import ThreadStoppedException
from controllers.controller import Controller
from smartnet.message import Message
from smartnet.message_log_constants import MessageLogCode, SeverityCode
from smartnet.parameter_registry import get_parameter
from tools.validate_scenarios import ScenarioValidator
import smartnet.constants as snc


class TestMonitoringCanParameter(unittest.TestCase):
	def setUp(self):
		self.controller = object.__new__(Controller)
		self.controller._controllerId = 209

	def test_read_write_wire_format_and_readback(self):
		state = [0]
		packets = []

		def respond(message, *args):
			data = list(message.get_data())
			packets.append((message.get_program_type(), message.getProgramId(),
				message.getFunctionId(), message.getRequestFlag(), data.copy()))
			if message.getFunctionId() == snc.RemoteControlFunction.SET_PARAMETER_VALUE:
				state[0] = data[2]
				data.append(snc.RemoteControlSetParameterResult.SET_PARAMETER_STATUS_OK)
			else:
				data.append(state[0])
			return Message(message.get_program_type(), message.getProgramId(),
				message.getFunctionId(), snc.RequestFlag.RESPONSE, data)

		with patch.object(Message, 'send', autospec=True, side_effect=respond):
			self.assertEqual(self.controller.read_monitoring_enabled(), 0)
			self.assertTrue(self.controller.write_monitoring_enabled(1))
			self.assertTrue(self.controller.write_monitoring_enabled(0))
		self.assertEqual([packet[4] for packet in packets], [
			[snc.ProgramType.CONTROLLER, 45],
			[snc.ProgramType.CONTROLLER, 45, 1],
			[snc.ProgramType.CONTROLLER, 45],
			[snc.ProgramType.CONTROLLER, 45, 0],
			[snc.ProgramType.CONTROLLER, 45],
		])
		self.assertTrue(all(packet[0] == snc.ProgramType.REMOTE_CONTROL
			and packet[1] == 209 and packet[3] == snc.RequestFlag.REQUEST for packet in packets))
		self.assertEqual(get_parameter(snc.ProgramType.CONTROLLER, 45).type, 'UINT8_T')

	def test_unavailable_read_and_unconfirmed_write(self):
		with patch('controllers.controller.sr.RemoteControlParameter') as parameter:
			parameter.return_value.read.return_value = False
			parameter.return_value.write.return_value = False
			self.assertIsNone(self.controller.read_monitoring_enabled())
			self.assertFalse(self.controller.write_monitoring_enabled(1))
			parameter.return_value.read.assert_called_once()

	def test_readback_mismatch_fails_write(self):
		with patch('controllers.controller.sr.RemoteControlParameter') as parameter:
			parameter.return_value.write.return_value = True
			parameter.return_value.read.return_value = True
			parameter.return_value.get_value.return_value = 0
			self.assertFalse(self.controller.write_monitoring_enabled(1))

	def test_invalid_boolean_is_rejected(self):
		with patch('controllers.controller.sr.RemoteControlParameter') as parameter:
			self.assertFalse(self.controller.write_monitoring_enabled(2))
			parameter.assert_not_called()


class TestJournalControllerScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = Scenario.__new__(Scenario)
		self.host = self.scenario._controllerHost = Mock()
		self.host.read_monitoring_enabled.return_value = 0
		self.host.write_monitoring_enabled.return_value = True
		self.scenario.find_unused_controller_id = Mock(return_value=255)
		self.scenario.snapshot_journal = Mock(return_value=True)
		self.scenario.wait_journal_entry = Mock(return_value=True)
		self.scenario.wait = Mock()
		self.emitter = Mock()
		self.scenario.make_presence_emitter = Mock(return_value=self.emitter)

	def test_success_restores_monitoring_after_source_stops(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.host.write_monitoring_enabled.call_args_list,
			[unittest.mock.call(1), unittest.mock.call(0)])
		self.emitter.start.assert_called_once()
		self.emitter.stop.assert_called_once()
		self.scenario.wait.assert_has_calls([
			unittest.mock.call(self.scenario.ANNOUNCEMENT_SECONDS),
			unittest.mock.call(self.scenario.CONNECTION_LOSS_SECONDS),
		])
		self.scenario.wait_journal_entry.assert_called_once_with(
			MessageLogCode.MLC_CONTROLLER_CONNECTION_ERROR, SeverityCode.SC_ERROR,
			255, self.scenario.JOURNAL_TIMEOUT)

	def test_enabled_monitoring_is_not_written(self):
		self.host.read_monitoring_enabled.return_value = 1
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.host.write_monitoring_enabled.assert_not_called()

	def test_unavailable_monitoring_does_not_announce(self):
		self.host.read_monitoring_enabled.return_value = None
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.host.write_monitoring_enabled.assert_not_called()
		self.scenario.make_presence_emitter.assert_not_called()

	def test_failed_enable_still_restores_original_state(self):
		self.host.write_monitoring_enabled.side_effect = [False, True]
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.host.write_monitoring_enabled.call_args_list,
			[unittest.mock.call(1), unittest.mock.call(0)])
		self.scenario.make_presence_emitter.assert_not_called()

	def test_failed_snapshot_restores_monitoring(self):
		self.scenario.snapshot_journal.return_value = False
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.host.write_monitoring_enabled.assert_called_with(0)
		self.scenario.make_presence_emitter.assert_not_called()

	def test_journal_timeout_restores_monitoring(self):
		self.scenario.wait_journal_entry.return_value = False
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.host.write_monitoring_enabled.assert_called_with(0)

	def test_no_free_id_restores_without_announcing(self):
		self.scenario.find_unused_controller_id.return_value = None
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.host.write_monitoring_enabled.assert_called_with(0)
		self.scenario.make_presence_emitter.assert_not_called()

	def test_cancel_while_announcing_stops_source_and_restores(self):
		self.scenario.wait.side_effect = ThreadStoppedException('test cancellation')
		with self.assertRaises(ThreadStoppedException):
			self.scenario.run()
		self.emitter.stop.assert_called_once()
		self.host.write_monitoring_enabled.assert_called_with(0)
		self.assertEqual(self.scenario._status, 'FAIL')

	def test_cancel_while_silent_restores(self):
		self.scenario.wait.side_effect = [True, ThreadStoppedException('test cancellation')]
		with self.assertRaises(ThreadStoppedException):
			self.scenario.run()
		self.emitter.stop.assert_called_once()
		self.host.write_monitoring_enabled.assert_called_with(0)

	def test_cleanup_failure_overrides_success(self):
		for failure in (False, RuntimeError('CAN disconnected')):
			with self.subTest(failure=failure):
				self.host.write_monitoring_enabled.side_effect = [True, failure]
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')

	def test_preset_free_initialization_leaves_programs_untouched(self):
		self.scenario._manualSensorsList = []
		self.scenario._virtual_outdoor = None
		with patch('scenario.scenario.main.loadPreset') as load, \
				patch.object(self.scenario, '_activate_virtual_outdoor') as activate:
			self.scenario.init_scenario()
			self.scenario.clear()
		load.assert_not_called()
		activate.assert_not_called()
		self.host.get_program_list.assert_not_called()
		self.assertEqual(self.scenario._programList, {})
		self.assertEqual(self.scenario.get_estimated_duration(), Scenario.ESTIMATED_RUN_SECONDS)

	def test_validator_accepts_explicit_no_preset(self):
		root = Path(__file__).resolve().parents[1]
		validator = ScenarioValidator(root)
		validator.validate_file(root / 'scenario/list/journal/scenario_journal_9_14.py')
		self.assertEqual(validator.errors, [])


class TestControllerPresence(unittest.TestCase):
	def test_announcements_have_distinct_controller_identity(self):
		scenario = JournalControllerScenario.__new__(JournalControllerScenario)
		message = scenario.make_presence_emitter(255)._messages[0]
		self.assertEqual(message.get_program_type(), snc.ProgramType.CONTROLLER)
		self.assertEqual(message.getProgramId(), 255)
		self.assertEqual(message.getFunctionId(), snc.ControllerFunction.I_AM_HERE)
		self.assertEqual(message.getRequestFlag(), snc.RequestFlag.RESPONSE)
		self.assertEqual(message.get_data(), [snc.ControllerType.SWK_1])

	def test_collector_ignores_requests_and_other_program_types(self):
		collector = ControllerPresenceCollector()
		for program_type, flag, controller_id in (
			(snc.ProgramType.CONTROLLER, snc.RequestFlag.REQUEST, 255),
			(snc.ProgramType.BOILER, snc.RequestFlag.RESPONSE, 254),
			(snc.ProgramType.CONTROLLER, snc.RequestFlag.RESPONSE, 253),
		):
			collector.on_can_message_received(Message(program_type, controller_id,
				snc.ControllerFunction.I_AM_HERE, flag, [snc.ControllerType.SWK_1]))
		collector.on_can_message_received(None)
		self.assertEqual(collector.get_ids(), {253})

	def test_discovery_excludes_host_virtual_io_and_online_controllers(self):
		scenario = JournalControllerScenario.__new__(JournalControllerScenario)
		scenario._controllerHost = Mock()
		scenario._controllerHost.get_controller_id.return_value = 255
		scenario._sim = Mock()
		virtual_io = Mock()
		virtual_io.get_id.return_value = 254
		scenario._sim.getControllersIOList.return_value = [virtual_io]
		with patch('scenario.base.journal_controller.CanListener.subscribe') as subscribe, \
				patch('scenario.base.journal_controller.CanListener.unsubscribe') as unsubscribe, \
				patch.object(Message, 'send') as send:
			def observe(delay):
				subscribe.call_args.args[0].on_can_message_received(Message(
					snc.ProgramType.CONTROLLER, 253, snc.ControllerFunction.I_AM_HERE,
					snc.RequestFlag.RESPONSE, [snc.ControllerType.SWK_1]))
			scenario.wait = Mock(side_effect=observe)
			self.assertEqual(scenario.find_unused_controller_id(), 252)
			send.assert_called_once()
			unsubscribe.assert_called_once_with(subscribe.call_args.args[0])

	def test_discovery_unsubscribes_when_cancelled(self):
		scenario = JournalControllerScenario.__new__(JournalControllerScenario)
		scenario.wait = Mock(side_effect=ThreadStoppedException('cancel discovery'))
		with patch('scenario.base.journal_controller.CanListener.subscribe') as subscribe, \
				patch('scenario.base.journal_controller.CanListener.unsubscribe') as unsubscribe, \
				patch.object(Message, 'send'):
			with self.assertRaises(ThreadStoppedException):
				scenario.find_unused_controller_id()
			unsubscribe.assert_called_once_with(subscribe.call_args.args[0])

	def test_full_bus_has_no_free_id(self):
		scenario = JournalControllerScenario.__new__(JournalControllerScenario)
		scenario._controllerHost = Mock()
		scenario._controllerHost.get_controller_id.return_value = 123
		scenario._sim = Mock()
		scenario._sim.getControllersIOList.return_value = []
		scenario.wait = Mock()
		with patch('scenario.base.journal_controller.ControllerPresenceCollector') as collector, \
				patch('scenario.base.journal_controller.CanListener.subscribe'), \
				patch('scenario.base.journal_controller.CanListener.unsubscribe'), \
				patch.object(Message, 'send'):
			collector.return_value.get_ids.return_value = set(range(1, 256))
			self.assertIsNone(scenario.find_unused_controller_id())


if __name__ == '__main__':
	unittest.main()

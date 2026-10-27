"""Controller-reply fixtures for scenario orchestration, not firmware integration."""

from datetime import datetime, timedelta
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, call, patch

import smartnet.constants as snc


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
	spec = importlib.util.spec_from_file_location(name, ROOT / path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def load_scenarios():
	parent = ModuleType('scenario.scenario')
	parent.Scenario = type('Parent', (), {})
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	message = ModuleType('smartnet.message')
	message.Message = Mock()
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	with patch.dict(sys.modules, {
		'scenario.scenario': parent, 'smartnet.remoteControl': remote,
		'smartnet.message': message, 'consoleLog': console,
	}):
		protocol = load_module('room_protocol_test', 'smartnet/room.py')
		with patch.dict(sys.modules, {'smartnet.room': protocol}):
			base = load_module('scenario.base.room', 'scenario/base/room.py')
			with patch.dict(sys.modules, {'scenario.base.room': base}):
				scenarios = [load_module(f'room_scenario_{index}',
					f'scenario/list/room/scenario_room_3_2_{index}.py') for index in (2, 3, 4)]
	return protocol, base, scenarios


protocol, base, scenarios = load_scenarios()
P = snc.RoomDeviceParameterId
M = snc.RoomWorkMode


class TestRoomProtocol(unittest.TestCase):
	def test_group_message_wire_fields(self):
		with patch.object(protocol, 'Message') as message:
			protocol.make_group_work_mode_message(7, M.ECONOM)
			message.assert_called_once_with(snc.ProgramType.ROOM_DEVICE, 0, 2,
				snc.RequestFlag.REQUEST, [7, 1])

	def test_invalid_group_and_mode_are_rejected(self):
		for group in (0, -1, 256, True, 1.5, None):
			with self.subTest(group=group), self.assertRaises(ValueError):
				protocol.make_group_work_mode_message(group, M.COMFORT)
		with self.assertRaises(ValueError):
			protocol.make_group_work_mode_message(1, 4)

	def test_group_parameter_is_registered(self):
		from smartnet.parameter_registry import get_parameter
		self.assertEqual(int(P.GROUP), 40)
		self.assertEqual(get_parameter(snc.ProgramType.ROOM_DEVICE, P.GROUP).type, 'UINT8_T')


class TestRoomSchedule(unittest.TestCase):
	def test_window_has_controller_relative_minutes(self):
		now = datetime(2026, 10, 27, 12, 34, 59)
		start, end, table = base.RoomScenario._schedule_window(now, 4)
		self.assertEqual(start, datetime(2026, 10, 27, 12, 38))
		self.assertEqual(end - start, timedelta(minutes=2))
		self.assertEqual(table[4, 0], (758, 760))
		self.assertEqual(len(table), 21)
		self.assertEqual(sum(value != (0, 0) for value in table.values()), 1)

	def test_window_crosses_midnight_and_week(self):
		now = datetime(2026, 12, 31, 23, 55, 59)
		start, end, table = base.RoomScenario._schedule_window(now, 6)
		self.assertEqual(start, datetime(2026, 12, 31, 23, 59))
		self.assertEqual(end, datetime(2027, 1, 1, 0, 1))
		self.assertEqual(table[6, 0], (1439, 1440))
		self.assertEqual(table[0, 0], (0, 1))

	def test_window_entirely_on_next_controller_day(self):
		now = datetime(2026, 10, 27, 23, 59)
		_, _, table = base.RoomScenario._schedule_window(now, 6)
		self.assertEqual(table[0, 0], (3, 5))
		self.assertEqual(table[6, 0], (0, 0))

	def test_clock_retries_midnight_and_uses_controller_id(self):
		scenario = base.RoomScenario()
		scenario._controllerHost = Mock()
		scenario._controllerHost.get_controller_id.return_value = 123
		before = (31, 6, 12, 2026)
		after = (1, 0, 1, 2027)
		values = iter([before, (23, 59, 59, 0), after, after, (0, 0, 1, 0), after])
		def parameter(**kwargs):
			self.assertEqual(kwargs['programId'], 123)
			self.assertEqual(kwargs['programType'], snc.ProgramType.CONTROLLER)
			return Mock(read=Mock(return_value=True), get_value=Mock(return_value=next(values)))
		with patch.object(base, 'RemoteControlParameter', side_effect=parameter):
			self.assertEqual(scenario._read_controller_clock(), (datetime(2027, 1, 1, 0, 0, 1), 0))

	def test_missing_clock_is_failure_without_pc_time_fallback(self):
		scenario = base.RoomScenario()
		scenario._controllerHost = Mock()
		with patch.object(base, 'RemoteControlParameter', return_value=Mock(read=Mock(return_value=False))):
			with self.assertRaises(base.RoomCheckFailed):
				scenario._read_controller_clock()

	def test_schedule_checks_both_real_transitions(self):
		scenario = base.RoomScenario()
		scenario._rooms = [Mock()]
		now = datetime(2026, 10, 27, 23, 55)
		start, end, _ = scenario._schedule_window(now, 6)
		scenario._read_controller_clock = Mock(side_effect=[(now, 6), (now, 6), (start, 6)])
		scenario._put = Mock()
		scenario._expect_temperature = Mock()
		scenario._wait_controller_time = Mock()
		scenario._check_schedule()
		self.assertEqual(scenario._expect_temperature.call_args_list, [
			call(M.PROGRAM, scenario.ECONOM_TEMPERATURE),
			call(M.PROGRAM, scenario.COMFORT_TEMPERATURE),
			call(M.PROGRAM, scenario.ECONOM_TEMPERATURE),
		])
		self.assertEqual(scenario._wait_controller_time.call_args_list, [call(start), call(end)])
		self.assertEqual(scenario._put.call_count, 22)

	def test_slow_schedule_write_fails_before_automatic_mode(self):
		scenario = base.RoomScenario()
		scenario._rooms = [Mock()]
		now = datetime(2026, 10, 27, 12)
		scenario._read_controller_clock = Mock(side_effect=[(now, 1), (now + timedelta(minutes=4), 1)])
		scenario._put = Mock()
		with self.assertRaises(base.RoomCheckFailed):
			scenario._check_schedule()
		self.assertEqual(scenario._put.call_count, 21)


class TestRoomRestoration(unittest.TestCase):
	def setUp(self):
		self.scenario = scenarios[0].Scenario()
		self.rooms = [Mock() for _ in range(4)]
		for index, room in enumerate(self.rooms):
			room.get_id.return_value = 101 + index
		self.scenario._programList = dict(zip(self.scenario.get_required_programs(), self.rooms))
		self.initial = {}
		for index, room in enumerate(self.rooms):
			self.initial[room.get_id(), P.GROUP, None] = (7, 7, 9, 0)[index]
			self.initial[room.get_id(), P.WORK_MODE, None] = index
		for parameter, value in ((P.ROOM_COMFORT_TEMPERATURE, 21),
				(P.ROOM_REDUCED_TEMPERATURE, 16), (P.ROOM_OFF_TEMPERATURE, 7)):
			self.initial[101, parameter, None] = value
		for day in range(7):
			for period in range(3):
				self.initial[101, P.SCHEDULE, (day, period)] = (day * 60, day * 60 + period)
		self.values = self.initial.copy()
		self.scenario._read = Mock(side_effect=lambda room, item, index=None:
			self.values[room.get_id(), item, index])
		self.scenario._put = Mock(side_effect=self.write)

	def write(self, room, item, value, index=None):
		self.values[room.get_id(), item, index] = value

	def test_success_restores_all_settings_and_schedule(self):
		def sequence():
			self.scenario._put(self.rooms[0], P.SCHEDULE, (0, 0), (3, 1))
		self.scenario._run_test(sequence)
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.values, self.initial)
		calls = self.scenario._put.call_args_list
		self.assertEqual(calls[-4:], [call(room, P.GROUP, group, None)
			for room, group in zip(self.rooms, (7, 7, 9, 0))])

	def test_failure_restores_all_settings(self):
		self.scenario._run_test(Mock(side_effect=base.RoomCheckFailed('test failure')))
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.values, self.initial)

	def test_cancellation_restores_all_settings(self):
		with self.assertRaises(RuntimeError):
			self.scenario._run_test(Mock(side_effect=RuntimeError('cancelled')))
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.values, self.initial)

	def test_missing_snapshot_does_not_modify_anything(self):
		self.scenario._read.side_effect = base.RoomCheckFailed('no response')
		self.scenario._run_test(Mock())
		self.scenario._put.assert_not_called()
		self.assertEqual(self.scenario._status, 'FAIL')

	def test_cleanup_failure_does_not_stop_remaining_restoration(self):
		def write(room, item, value, index=None):
			if item == P.ROOM_COMFORT_TEMPERATURE and value == 21:
				raise base.RoomCheckFailed('no acknowledgement')
			self.write(room, item, value, index)
		self.scenario._put.side_effect = write
		self.scenario._run_test(Mock())
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.values[104, P.WORK_MODE, None], 3)
		self.assertEqual(self.values[101, P.GROUP, None], 7)

	def test_broadcast_sequence_checks_every_group_mode(self):
		self.scenario._rooms = self.rooms
		self.scenario._expect_modes = Mock()
		with patch.object(base, 'set_group_work_mode') as send:
			self.scenario._group_sequence(broadcast=True)
			self.assertEqual(send.call_args_list, [call(1, mode) for mode in (M.COMFORT, M.ECONOM, M.PROGRAM, M.OFF)])
		self.assertEqual(self.scenario._expect_modes.call_args_list,
			[call([mode] * 3 + [M.OFF]) for mode in (M.COMFORT, M.ECONOM, M.PROGRAM, M.OFF)])

	def test_individual_sequence_uses_each_room_as_source(self):
		self.scenario._rooms = self.rooms
		self.scenario._expect_modes = Mock()
		self.scenario._group_sequence(broadcast=False)
		mode_writes = [item for item in self.scenario._put.call_args_list if item.args[1] == P.WORK_MODE]
		self.assertEqual(mode_writes, [call(room, P.WORK_MODE, mode)
			for room in self.rooms[:3] for mode in (M.COMFORT, M.ECONOM, M.PROGRAM, M.OFF)])

	def test_schedule_write_requires_readback_confirmation(self):
		scenario = base.RoomScenario()
		scenario._parameter = Mock(return_value=Mock(write=Mock(return_value=True)))
		scenario._read = Mock(return_value=(0, 0))
		with self.assertRaises(base.RoomCheckFailed):
			scenario._put(self.rooms[0], P.SCHEDULE, (60, 120), (0, 0))


if __name__ == '__main__':
	unittest.main()

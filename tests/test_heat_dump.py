"""Heat-dump checks requiring neither GUI, CAN hardware nor a controller."""

import importlib
import unittest
from unittest.mock import Mock, patch


class HeatDumpTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		# Preserve the application's existing message/mainThread circular import order.
		importlib.import_module('mainThread')
		cls.cooling = importlib.import_module('smartnet.cooling')
		cls.scenarios = importlib.import_module('scenario.base.heat_dump')
		cls.presets = importlib.import_module('presets.list.heat_dump')
		cls.constants = importlib.import_module('smartnet.constants')

	def test_cooling_request_matches_temperature_source_wire_format(self):
		on = self.cooling.make_cooling_request(200, True)
		off = self.cooling.make_cooling_request(200, False)
		self.assertEqual(on.getHeader(), 0x00030003)
		self.assertEqual(bytes(on.get_data()), b'\xc8\x01')
		self.assertEqual(bytes(off.get_data()), b'\xc8\x00')
		with self.assertRaises(ValueError):
			self.cooling.make_cooling_request(0, True)
		with self.assertRaises(ValueError):
			self.cooling.make_cooling_request(True, True)

	def test_publication_propagates_transport_failure(self):
		bus = Mock()
		bus.send.side_effect = RuntimeError('CAN disconnected')
		with patch.object(self.cooling, 'CanBusInterface') as transport:
			transport.return_value.get.return_value = bus
			with self.assertRaisesRegex(RuntimeError, 'CAN disconnected'):
				self.cooling.send_cooling_request(200, True)

	def test_room_request_observer_checks_circuit_and_state(self):
		from smartnet.message import Message
		observer = self.scenarios.RoomCoolingObserver(self.presets.CIRCUIT_ID)
		def request(circuit, state):
			return Message(self.constants.ProgramType.ROOM_DEVICE, 0, 1,
				self.constants.RequestFlag.REQUEST, bytes((circuit, state)))
		observer.on_can_message_received(request(self.presets.CIRCUIT_ID, 0))
		observer.on_can_message_received(request(self.presets.CIRCUIT_ID + 1, 1))
		self.assertFalse(observer.observed)
		observer.on_can_message_received(request(self.presets.CIRCUIT_ID, 1))
		self.assertTrue(observer.observed)

	def test_preset_has_two_valves_and_no_real_boiler(self):
		from presets.preset import validate_program_presets
		programs, hosts = self.presets.get_presets_list()
		validate_program_presets(programs)
		self.assertEqual({host.get_id() for host in hosts}, {123, 124, 125, 126})
		self.assertFalse(any(p.get_type() == self.constants.ProgramType.BOILER for p in programs))
		rooms = [p for p in programs if p.get_type() == self.constants.ProgramType.ROOM_DEVICE]
		self.assertEqual(len(rooms), 2)
		self.assertTrue(rooms[0].get_outputs()[0].is_mapped())
		self.assertTrue(rooms[1].get_outputs()[1].is_mapped())
		self.assertEqual(rooms[0].getSettings().getSourceList()[0], self.presets.CIRCUIT_ID)
		self.assertEqual(rooms[1].getSettings().getSourceList()[1], self.presets.CIRCUIT_ID)

	def test_room_scenarios_drive_normally_open_valve(self):
		for checklist, states, allowed in (
			('6_5_1', (255, 0), 1),
			('6_5_2', (255, 255, 0, 255), 0),
		):
			with self.subTest(checklist=checklist):
				module = importlib.import_module(f'scenario.list.room.scenario_room_{checklist}')
				scenario = object.__new__(module.Scenario)
				circuit = Mock()
				room = Mock()
				valve = room.get_output_channel.return_value
				valve.is_mapped.return_value = True
				valve.get_value.side_effect = states
				scenario._programList = {'circuit': circuit, 'room_1': room}
				scenario.wait_state_permanence = lambda predicate, duration, timeout: predicate()
				def run(settings, sensors, baseline, active):
					self.assertEqual(settings[-1], (room, self.constants.ProgramType.ROOM_DEVICE,
						self.constants.RoomDeviceParameterId.ROOM_DEVICE_VALVE_STATE, 0, None))
					self.assertIn((room, self.constants.ProgramType.ROOM_DEVICE,
						self.constants.RoomDeviceParameterId.HEAT_EXTRICATION, allowed, 0), settings)
					baseline()
					active()
				scenario.run_heat_dump = run
				scenario.run()
				self.assertEqual(valve.get_value.call_count, len(states))
				if checklist == '6_5_2':
					self.assertEqual(room.get_temperature.return_value.set_value.call_count, 2)

	def test_room_valve_setting_restored_on_success_and_failure(self):
		for fail in (False, True):
			with self.subTest(fail=fail):
				scenario = object.__new__(self.scenarios.HeatDumpScenario)
				room = Mock()
				room.get_id.return_value = 105
				scenario._programList = {'room_1': room}
				value = [1]  # Initial valve is normally closed.
				scenario._read = lambda p, t, i, index=None: value[0]
				scenario._put = lambda p, t, i, new_value, index=None: value.__setitem__(0, new_value)
				def active():
					self.assertEqual(value[0], scenario.NORMALLY_OPEN_VALVE_STATE)
					if fail:
						raise self.scenarios.HeatDumpFailed('expected failure')
				with patch.object(self.scenarios, 'send_cooling_request'):
					scenario.run_heat_dump([scenario.room_valve_setting('room_1')], [],
						lambda: None, active)
				self.assertEqual(value[0], 1)
				self.assertEqual(scenario._status, 'FAIL' if fail else 'OK')

	def test_success_and_failure_always_restore_inputs_and_cancel_cooling(self):
		for fail in (False, True):
			with self.subTest(fail=fail):
				scenario = object.__new__(self.scenarios.HeatDumpScenario)
				program = Mock()
				program.get_id.return_value = 101
				sensor = Mock()
				sensor.is_mapped.return_value = True
				sensor.get_value.return_value = 17
				sensor.isManual.return_value = True
				values = {('parameter', None): 0}
				scenario._read = lambda p, t, i, index=None: values[(i, index)]
				scenario._put = lambda p, t, i, value, index=None: values.__setitem__((i, index), value)
				calls = []
				with patch.object(self.scenarios, 'send_cooling_request',
					side_effect=lambda source, enabled: calls.append((source, enabled))):
					def active():
						if fail:
							raise self.scenarios.HeatDumpFailed('expected failure')
					scenario.run_heat_dump([(program, 'type', 'parameter', 1, None)],
						[(sensor, 35)], lambda: None, active)
				self.assertEqual(values[('parameter', None)], 0)
				self.assertEqual(calls, [(200, False), (200, True), (200, False)])
				self.assertEqual(scenario._status, 'FAIL' if fail else 'OK')
				self.assertEqual(sensor.set_value.call_args_list[-1].args, (17, True))
				sensor.set_manual.assert_called_with(True)

	def test_failed_enable_still_sends_disable(self):
		scenario = object.__new__(self.scenarios.HeatDumpScenario)
		sensor = Mock()
		sensor.is_mapped.return_value = True
		sensor.get_value.return_value = 17
		sensor.isManual.return_value = False
		calls = []
		def send(source, enabled):
			calls.append(enabled)
			if enabled:
				raise RuntimeError('CAN unavailable')
		with patch.object(self.scenarios, 'send_cooling_request', side_effect=send):
			with self.assertRaisesRegex(RuntimeError, 'CAN unavailable'):
				scenario.run_heat_dump([], [(sensor, 35)], lambda: None, lambda: None)
		self.assertEqual(calls, [False, True, False])
		self.assertEqual(scenario._status, 'FAIL')
		sensor.set_manual.assert_called_with(False)


if __name__ == '__main__':
	unittest.main()
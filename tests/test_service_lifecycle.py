"""Service shutdown tests with fake resources, not physical CAN or network devices."""

import threading
import unittest
from unittest.mock import Mock, patch

import debug
from scenario.scenario import ScenarioThread
from smartnet import message
from udp import udp


class TestCanLifecycle(unittest.TestCase):
	def test_close_stops_notifier_before_bus_and_is_idempotent(self):
		listener = object.__new__(message.CanListener)
		listener._closed = False
		listener._notifier = Mock()
		listener._canbus = Mock()
		events = []
		listener._notifier.stop.side_effect = lambda **kwargs: events.append('notifier')
		listener._canbus.shutdown.side_effect = lambda: events.append('bus')
		listener.close()
		listener.close()
		self.assertEqual(events, ['notifier', 'bus'])

	def test_notifier_failure_still_closes_bus(self):
		listener = object.__new__(message.CanListener)
		listener._closed = False
		listener._notifier = Mock()
		listener._notifier.stop.side_effect = RuntimeError('notifier failed')
		listener._canbus = Mock()
		with self.assertRaises(RuntimeError):
			listener.close()
		listener._canbus.shutdown.assert_called_once()

	def test_listener_can_unsubscribe_inside_callback(self):
		listener = object.__new__(message.CanListener)
		subscriber = Mock()
		subscriber.on_can_message_received.side_effect = (
			lambda msg: message.CanListener.unsubscribe(subscriber))
		frame = message.can.Message(arbitration_id=0, data=[], is_extended_id=True)
		with patch.object(message.CanListener, '_listeners', [subscriber]):
			thread = threading.Thread(target=listener.on_message_received,
				args=(frame,), daemon=True)
			thread.start()
			thread.join(1)
			self.assertFalse(thread.is_alive(), 'Callback deadlocked during unsubscribe')
			self.assertEqual(message.CanListener._listeners, [])


class TestUdpLifecycle(unittest.TestCase):
	def test_partial_start_closes_previously_created_socket_and_bus(self):
		bus = Mock()
		first = Mock(ident=None)
		first.is_alive.return_value = False
		with patch.object(udp, 'UdpCanBusInterface') as interface, \
				patch.object(udp, 'udp_listen_thread', return_value=first), \
				patch.object(udp, 'can_thread', side_effect=OSError('cannot create sender')):
			interface.return_value.get.return_value = bus
			with self.assertRaisesRegex(OSError, 'cannot create sender'):
				udp.init_udp_bridge(31987)
		first._sock.close.assert_called_once()
		bus.shutdown.assert_called_once()

	def test_bind_failure_closes_receiver_socket_and_bus(self):
		bus = Mock()
		sock = Mock()
		sock.bind.side_effect = OSError('port is in use')
		with patch.object(udp, 'UdpCanBusInterface') as interface, \
				patch.object(udp.socket, 'socket', return_value=sock):
			interface.return_value.get.return_value = bus
			with self.assertRaisesRegex(OSError, 'port is in use'):
				udp.init_udp_bridge(31987)
		sock.close.assert_called_once()
		bus.shutdown.assert_called_once()

	def test_bridge_stop_signals_and_joins_both_threads_before_bus(self):
		bridge = object.__new__(udp.UdpBridge)
		bridge._closed = False
		bridge._threads = [Mock(ident=1), Mock(ident=2)]
		bridge._canbus = Mock()
		events = []
		for thread in bridge._threads:
			thread.is_alive.return_value = False
			thread.join.side_effect = lambda timeout: events.append('join')
		bridge._canbus.shutdown.side_effect = lambda: events.append('bus')
		bridge.stop()
		bridge.stop()
		self.assertEqual(events, ['join', 'join', 'bus'])
		for thread in bridge._threads:
			thread._stop_event.set.assert_called_once()


class TestScenarioLifecycle(unittest.TestCase):
	def test_exit_always_runs_scenario_cleanup(self):
		thread = object.__new__(ScenarioThread)
		thread.run_scenarios = Mock(side_effect=RuntimeError('unexpected failure'))
		thread.stop_scenario_now = Mock()
		with self.assertRaisesRegex(RuntimeError, 'unexpected failure'):
			thread.run()
		thread.stop_scenario_now.assert_called_once()


class TestDebugLifecycle(unittest.TestCase):
	def test_stop_handles_notifier_reentry_and_closes_bus_once(self):
		responder = object.__new__(debug.debug_thread)
		responder._closed = False
		responder._heartbeat = Mock(ident=1)
		responder._heartbeat.is_alive.return_value = False
		responder._notifier = Mock()
		responder._notifier.stop.side_effect = lambda **kwargs: responder.stop()
		responder._canbus = Mock()
		responder.stop()
		responder.stop()
		responder._heartbeat._stop_event.set.assert_called_once()
		responder._notifier.stop.assert_called_once()
		responder._canbus.shutdown.assert_called_once()


if __name__ == '__main__':
	unittest.main()
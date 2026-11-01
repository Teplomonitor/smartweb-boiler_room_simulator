"""Service shutdown tests with fake resources, not physical CAN or network devices."""

import threading
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import debug
from scenario import scenario as scenarios
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
	def test_scenario_thread_requires_dependencies_on_first_creation(self):
		# A fresh process prevents an existing singleton from masking the first call.
		script = textwrap.dedent('''\
			import threading
			from types import SimpleNamespace
			from unittest.mock import Mock, patch
			from scenario import scenario as scenarios
			ScenarioThread = scenarios.ScenarioThread
			worker = SimpleNamespace(ready_event=threading.Event(), taskEnable=lambda: True,
			    _scenario_thread=None)
			with patch.object(scenarios.mainThread, 'MainThread', return_value=worker):
			    scenarios.start_scenario('test.py')
			    scenarios.stop_scenario()
			assert not hasattr(ScenarioThread, 'instance')
			for args in ((), (Mock(), None), (None, Mock())):
			    try:
			        ScenarioThread(*args)
			    except RuntimeError:
			        pass
			    else:
			        raise AssertionError('Created scenario thread without dependencies')
			    assert not hasattr(ScenarioThread, 'instance')
			controller, simulator = Mock(), Mock()
			with patch.object(ScenarioThread, 'start') as start:
			    thread = ScenarioThread(controller, simulator)
			    assert ScenarioThread() is thread
			    assert thread._controllerHost is controller
			    assert thread._simulator is simulator
			    start.assert_called_once()
			    worker._scenario_thread = thread
			    worker.ready_event.set()
			    with patch.object(scenarios.mainThread, 'MainThread', return_value=worker), \\
			            patch.object(thread, 'is_alive', return_value=True):
			        scenarios.start_scenario('test.py')
			        assert thread._newScenario == 'test.py'
			''')
		result = subprocess.run([sys.executable, '-c', script],
			cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=15)
		self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

	def test_gui_commands_reject_unavailable_worker_without_creating_thread(self):
		thread = Mock()
		thread.is_alive.return_value = True
		worker = SimpleNamespace(ready_event=threading.Event(), taskEnable=Mock(return_value=True),
			_scenario_thread=thread)
		with (patch.object(scenarios.mainThread, 'MainThread', return_value=worker),
				patch.object(scenarios, 'ScenarioThread') as factory,
				patch.object(scenarios, 'print_error') as log):
			scenarios.start_scenario('test.py')
			scenarios.stop_scenario()
			self.assertEqual(log.call_count, 2)
			factory.assert_not_called()
			thread.start_scenario.assert_not_called()
			thread._stopScenarioEvent.set.assert_not_called()
			worker.ready_event.set()
			scenarios.start_scenario('test.py')
			scenarios.stop_scenario()
			thread.start_scenario.assert_called_once_with('test.py')
			thread._stopScenarioEvent.set.assert_called_once()
			factory.assert_not_called()

	def test_gui_commands_reject_stopped_or_missing_worker(self):
		thread = Mock()
		worker = SimpleNamespace(ready_event=threading.Event(), taskEnable=Mock(return_value=True),
			_scenario_thread=thread)
		worker.ready_event.set()
		with patch.object(scenarios, 'print_error') as log:
			with patch.object(scenarios.mainThread, 'MainThread', side_effect=RuntimeError('not started')):
				scenarios.start_scenario('test.py')
			with patch.object(scenarios.mainThread, 'MainThread', return_value=worker):
				worker.taskEnable.return_value = False
				scenarios.start_scenario('test.py')
				worker.taskEnable.return_value = True
				thread.is_alive.return_value = False
				scenarios.start_scenario('test.py')
				worker._scenario_thread = None
				scenarios.start_scenario('test.py')
		self.assertEqual(log.call_count, 4)
		thread.start_scenario.assert_not_called()

	def test_initialization_failure_logs_traceback(self):
		thread = object.__new__(ScenarioThread)
		thread._newScenario = 'test.py'
		thread._currentScenario = None
		thread._stopScenarioEvent = threading.Event()
		thread.start_scenario_now = Mock(side_effect=AttributeError('missing controller'))
		thread.stop_scenario_now = Mock()
		thread._report_failure = Mock()
		with (patch.object(scenarios.mainThread, 'taskEnable', side_effect=[True, False]),
				patch.object(scenarios.time, 'sleep'), patch.object(scenarios, 'print_error') as log):
			thread.run_scenarios()
		messages = '\n'.join(call.args[0] for call in log.call_args_list)
		self.assertIn('Scenario initialization failed', messages)
		self.assertIn('Traceback (most recent call last)', messages)
		self.assertIn('AttributeError: missing controller', messages)
		thread.stop_scenario_now.assert_called_once_with('failed')
		thread._report_failure.assert_called_once()

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
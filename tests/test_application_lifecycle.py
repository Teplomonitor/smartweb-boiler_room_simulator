"""Lifecycle regression tests; no GUI, CAN adapter or external controller required."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import textwrap
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from application import Application


class WaitingWorker(threading.Thread):
	def __init__(self, args, gui, stop_event):
		super().__init__(name='test worker', daemon=True)
		self.stop_event = stop_event
		self.error = None
		self.cleanup_complete = False
		self.args = args

	def run(self):
		self.stop_event.wait()
		self.cleanup_complete = True


class TestApplicationLifecycle(unittest.TestCase):
	def setUp(self):
		# Some legacy tests install a mainThread stub globally. Load the real
		# compatibility layer independently so these tests also work in isolation.
		path = Path(__file__).resolve().parents[1] / 'mainThread.py'
		spec = importlib.util.spec_from_file_location('lifecycle_main_thread', path)
		self.runtime = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(self.runtime)
		modules = patch.dict(sys.modules, {'mainThread': self.runtime})
		modules.start()
		self.addCleanup(modules.stop)
		logging = patch.object(self.runtime.consoleLog, 'init_gui')
		logging.start()
		self.addCleanup(logging.stop)
		self.args = SimpleNamespace(gui=False, profile='test', udp=0,
			scenario='none', debug=False, can='virtual', id=0, preset='test')

	def make_application(self, **kwargs):
		app = Application(self.args, worker_factory=WaitingWorker, **kwargs)
		self.addCleanup(app.shutdown)
		return app

	def make_worker(self):
		with patch.object(self.runtime.config, 'ConfigParserInstance'):
			return self.runtime.ApplicationWorker(self.args, None, threading.Event())

	def test_construction_and_stop_before_start_create_no_services(self):
		factory = Mock()
		app = Application(self.args, worker_factory=factory)
		self.assertIsNone(app.worker)
		self.assertFalse(self.runtime.taskEnable())
		self.runtime.MainStop()
		self.assertTrue(app.shutdown())
		factory.assert_not_called()
		with self.assertRaisesRegex(RuntimeError, 'not been started'):
			self.runtime.MainThread()

	def test_explicit_start_and_idempotent_shutdown(self):
		app = self.make_application()
		app.start()
		self.assertIs(self.runtime.MainThread(), app.worker)
		self.assertTrue(self.runtime.taskEnable())
		self.runtime.MainStop()
		self.assertTrue(app.shutdown())
		self.assertFalse(app.worker.is_alive())
		self.assertFalse(self.runtime.taskEnable())
		self.assertTrue(app.shutdown())
		with self.assertRaises(RuntimeError):
			app.start()

	def test_second_application_cannot_replace_active_session(self):
		app = self.make_application()
		app.start()
		other = self.make_application()
		with self.assertRaisesRegex(RuntimeError, 'already active'):
			other.start()
		other.shutdown()
		self.assertIs(self.runtime.MainThread(), app.worker)
		self.assertTrue(self.runtime.taskEnable())

	def test_failed_worker_construction_closes_gui(self):
		self.args.gui = True
		gui = Mock()
		app = Application(self.args, gui_factory=Mock(return_value=gui),
			worker_factory=Mock(side_effect=ValueError('invalid configuration')))
		with self.assertRaisesRegex(ValueError, 'invalid configuration'):
			app.start()
		gui.stop.assert_called_once()
		self.assertFalse(self.runtime.taskEnable())

	def test_shutdown_timeout_is_reported_and_session_retained(self):
		app = self.make_application()
		app.worker = Mock(ident=1, error=None)
		app.worker.is_alive.return_value = True
		self.runtime.register_application(app)
		with patch.object(self.runtime.consoleLog, 'print_error') as log:
			self.assertFalse(app.shutdown(timeout=0))
			log.assert_called_once()
		self.assertIs(self.runtime.MainThread(), app.worker)
		app.worker.is_alive.return_value = False
		self.assertTrue(app.shutdown())

	def test_worker_constructor_does_not_start_a_thread(self):
		worker = self.make_worker()
		self.assertIsNone(worker.ident)
		self.assertFalse(worker.is_alive())

	def interactive_application(self):
		self.args.gui = True
		self.args.interactive_connection = True
		gui = Mock()
		app = self.make_application(gui_factory=Mock(return_value=gui))
		app.start()
		return app, gui

	def test_interactive_start_waits_for_connect(self):
		app, gui = self.interactive_application()
		self.assertIsNone(app.worker)
		self.assertFalse(self.runtime.taskEnable())
		gui.configure_connection.assert_called_once_with(app)
		self.assertTrue(app.shutdown())
		gui.stop.assert_called_once()

	def test_interactive_disconnect_keeps_window_and_reconnects(self):
		from connection_settings import DEFAULT_SETTINGS
		app, gui = self.interactive_application()
		app.connect(dict(DEFAULT_SETTINGS, controller_id=123, transport='udp', udp_port=32000))
		first = app.worker
		self.assertEqual((first.args.id, first.args.can, first.args.udp), (123, 'virtual', 32000))
		self.assertTrue(first.keep_gui_open)
		with self.assertRaises(RuntimeError):
			app.connect(DEFAULT_SETTINGS)
		app.disconnect()
		first.join(2)
		self.assertFalse(first.is_alive())
		self.assertFalse(app.closing)
		gui.stop.assert_not_called()
		with patch.object(self.runtime, 'reset_connection_services') as reset:
			app.connect(dict(DEFAULT_SETTINGS, can_context='canable0'))
			reset.assert_called_once()
		self.assertIsNot(app.worker, first)
		self.assertEqual((app.worker.args.can, app.worker.args.udp), ('canable0', 0))
		self.assertTrue(self.runtime.taskEnable())

	def test_interactive_reconnect_refuses_incomplete_cleanup(self):
		from connection_settings import DEFAULT_SETTINGS
		app, gui = self.interactive_application()
		app.connect(DEFAULT_SETTINGS)
		app.disconnect()
		app.worker.join(2)
		app.worker.cleanup_complete = False
		with self.assertRaisesRegex(RuntimeError, 'ресурсы'):
			app.connect(DEFAULT_SETTINGS)
		gui.stop.assert_not_called()

	def test_interactive_worker_cleanup_does_not_stop_gui(self):
		worker = self.make_worker()
		worker.keep_gui_open = True
		worker._guiThread = Mock()
		worker.clear()
		worker._guiThread.stop.assert_not_called()
		self.assertTrue(worker.cleanup_complete)

	def test_command_line_scenario_starts_after_worker_is_ready(self):
		self.args.scenario = 'test.py'
		worker = self.make_worker()
		thread = Mock()
		thread.is_alive.return_value = True

		def check_ready(path):
			self.assertTrue(worker.ready_event.is_set())
			self.assertEqual(path, 'test.py')

		thread.start_scenario.side_effect = check_ready
		with (patch.object(self.runtime.sm, 'CanListener'),
				patch.object(self.runtime.ctrlSearch, 'findOnlineController', return_value=123),
				patch.object(self.runtime.ss, 'Simulator'),
				patch.object(self.runtime.cc, 'Controller'),
				patch.object(self.runtime.ccio, 'initVirtualControllers'),
				patch.object(self.runtime.scenario, 'ScenarioThread', return_value=thread),
				patch.object(self.runtime.scenario.mainThread, 'MainThread', return_value=worker)):
			worker.initSimulator()
		thread.start_scenario.assert_called_once_with('test.py')

	def test_startup_failure_still_releases_owned_services(self):
		worker = self.make_worker()
		listener = Mock()
		def fail():
			worker._can_listener = listener
			raise ValueError('startup failed')
		worker.initSimulator = fail
		worker.start()
		worker.join(2)
		self.assertFalse(worker.is_alive())
		self.assertIsInstance(worker.error, ValueError)
		self.assertTrue(worker._taskStopEvent.is_set())
		listener.close.assert_called_once()

	def test_startup_preset_mismatch_keeps_session_ready_without_virtual_io(self):
		for parallel, selection in ((False, 'none'), (False, 'test.py'), (True, 'none')):
			with self.subTest(parallel=parallel, scenario=selection):
				self.args.can_worker = parallel
				self.args.scenario = selection
				worker = self.make_worker()
				worker._programPresetList = [object()]
				worker._controllerIoList = [object()]
				controller = Mock()
				controller.initController.return_value = False
				with (patch.object(self.runtime.sm, 'CanListener'),
						patch.object(self.runtime.ctrlSearch, 'findOnlineController', return_value=123),
						patch.object(self.runtime.ss, 'Simulator') as simulator,
						patch.object(self.runtime.cc, 'Controller', return_value=controller),
						patch.object(self.runtime.ccio, 'initVirtualControllers') as virtual_io,
						patch.object(self.runtime.scenario, 'ScenarioThread') as scenario_thread,
						patch.object(self.runtime.scenario, 'start_scenario') as start):
					worker.initSimulator()
				self.assertTrue(worker.ready_event.is_set())
				self.assertFalse(worker._taskStopEvent.is_set())
				self.assertIsNone(worker.error)
				controller.clear.assert_called_once()
				virtual_io.assert_not_called()
				simulator.return_value.reloadConfig.assert_called_once_with(controller, [])
				scenario_thread.assert_called_once_with(controller, simulator.return_value)
				if selection != 'none':
					start.assert_called_once_with(selection)
				else:
					start.assert_not_called()

	def test_controller_initialization_exception_is_not_a_preset_mismatch(self):
		worker = self.make_worker()
		with (patch.object(self.runtime.sm, 'CanListener'),
				patch.object(self.runtime.ctrlSearch, 'findOnlineController', return_value=123),
				patch.object(self.runtime.ss, 'Simulator'),
				patch.object(self.runtime.cc, 'Controller') as controller,
				patch.object(self.runtime.ccio, 'initVirtualControllers') as virtual_io):
			controller.return_value.initController.side_effect = OSError('CAN disconnected')
			with self.assertRaisesRegex(OSError, 'CAN disconnected'):
				worker.initSimulator()
		self.assertFalse(worker.ready_event.is_set())
		virtual_io.assert_not_called()

	def test_cleanup_joins_users_before_clearing_state_and_transports(self):
		worker = self.make_worker()
		events = []
		def thread(name):
			value = Mock(name=name)
			value.is_alive.return_value = False
			value.join.side_effect = lambda timeout: events.append(name)
			return value
		worker._scenario_thread = thread('scenario')
		worker._simulator = thread('simulator')
		worker._simulator._srt = thread('sensors')
		worker._simulator.clear.side_effect = lambda: events.append('state')
		worker._controller = Mock()
		worker._controller.clear.side_effect = lambda: events.append('controller')
		worker._can_listener = Mock()
		worker._can_listener.close.side_effect = lambda: events.append('CAN')
		worker.clear()
		self.assertEqual(events, ['scenario', 'simulator', 'sensors',
			'controller', 'state', 'CAN'])

	def test_cleanup_failure_does_not_skip_remaining_services(self):
		worker = self.make_worker()
		worker._debug_thread = Mock()
		worker._debug_thread.stop.side_effect = RuntimeError('debug cleanup failed')
		worker._udp_bridge = Mock()
		worker._can_listener = Mock()
		worker.clear()
		worker._udp_bridge.stop.assert_called_once()
		worker._can_listener.close.assert_called_once()
		self.assertIsInstance(worker.error, RuntimeError)


class TestVirtualCanShutdown(unittest.TestCase):
	def test_shutdown_during_discovery_releases_real_virtual_bus(self):
		# A fresh process avoids all test stubs and singleton state. No device,
		# UDP socket or preset is used: stop while discovery is still waiting.
		script = textwrap.dedent('''\
			import threading
			import time
			from types import SimpleNamespace
			from application import Application
			args = SimpleNamespace(gui=False, profile='main', udp=0,
			    scenario='none', debug=False, can='virtual', id=0,
			    preset='__not_loaded_during_discovery__')
			app = Application(args)
			app.start()
			try:
			    deadline = time.monotonic() + 5
			    while app.worker._can_listener is None and app.worker.is_alive():
			        assert time.monotonic() < deadline, 'CAN listener was not started'
			        time.sleep(0.01)
			    assert app.worker._can_listener is not None, app.worker.error
			finally:
			    assert app.shutdown(timeout=5), 'Shutdown timed out'
			assert app.worker.error is None, app.worker.error
			assert app.worker._can_listener._closed
			assert not [t.name for t in threading.enumerate()
			    if t is not threading.main_thread()], 'Background thread leaked'
			''')
		result = subprocess.run([sys.executable, '-c', script],
			cwd=Path(__file__).resolve().parents[1], capture_output=True,
			text=True, timeout=15)
		self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
	unittest.main()
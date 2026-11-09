"""Fresh-process connection checks to isolate legacy singleton/module state."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TestGuiConnection(unittest.TestCase):
	def run_script(self, script):
		result = subprocess.run([sys.executable, '-c', textwrap.dedent(script)],
			cwd=ROOT, capture_output=True, text=True, timeout=30)
		self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

	def test_no_arguments_defer_connection_but_cli_still_starts_normally(self):
		self.run_script('''\
			from unittest.mock import Mock, patch
			import main
			for argv, interactive in (([], True), (['--id', '123', '--can', 'virtual'], False),
			                          (['--no-gui'], False)):
			    app = Mock()
			    app.worker.error = None
			    with patch.object(main, 'Application', return_value=app) as factory:
			        assert main.main(argv) == 0
			        assert factory.call_args.args[0].interactive_connection is interactive
			        app.start.assert_called_once()
			''')

	def test_real_virtual_can_udp_and_model_threads_can_be_recreated(self):
		self.run_script('''\
			import os
			import socket
			import tempfile
			import threading
			import time
			from types import SimpleNamespace
			from unittest.mock import Mock, patch
			from application import Application
			from connection_settings import DEFAULT_SETTINGS
			import mainThread
			import smartnet.message as sm
			import udp.udp as udp
			def wait(predicate):
			    deadline = time.monotonic() + 5
			    while not predicate():
			        assert time.monotonic() < deadline, 'Connection timed out'
			        time.sleep(0.01)
			with tempfile.TemporaryDirectory() as directory:
			    os.environ['BRS_SETTINGS_PATH'] = os.path.join(directory, 'settings.ini')
			    args = SimpleNamespace(gui=True, interactive_connection=True, profile='main',
			        udp=0, scenario='none', debug=False, can='virtual', id=0, preset=None)
			    gui = Mock()
			    app = Application(args, gui_factory=lambda profile: gui)
			    app.start()
			    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			    sock.bind(('127.0.0.1', 0))
			    port = sock.getsockname()[1]
			    sock.close()
			    try:
			        with patch.object(mainThread.ctrlSearch, 'findOnlineController', side_effect=lambda value: value), \\
			             patch.object(mainThread.presets.preset, 'get_presets_list', return_value=([], [])), \\
			             patch.object(udp, 'send_broadcast_udp_packet'):
			            previous_controller = None
			            for transport, controller_id in (('can', 123), ('udp', 124), ('can', 125)):
			                app.connect(dict(DEFAULT_SETTINGS, transport=transport, controller_id=controller_id,
			                    can_context='virtual', udp_port=port))
			                worker = app.worker
			                wait(lambda: worker.ready_event.is_set() or not worker.is_alive())
			                assert worker.ready_event.is_set(), worker.error
			                assert worker._controller._controllerId == controller_id
			                assert worker._controller is not previous_controller
			                previous_controller = worker._controller
			                assert (worker._udp_bridge is not None) == (transport == 'udp')
			                app.disconnect()
			                worker.join(8)
			                assert not worker.is_alive(), 'Worker leaked'
			                assert worker.cleanup_complete and worker.error is None, worker.error
			                assert worker._can_listener._closed
			                gui.stop.assert_not_called()
			                assert not [t.name for t in threading.enumerate()
			                    if t is not threading.main_thread()], 'Service thread leaked'
			            with patch.object(sm, 'createBus', side_effect=RuntimeError('test connection failure')):
			                app.connect(dict(DEFAULT_SETTINGS, can_context='virtual'))
			                app.worker.join(5)
			                assert str(app.worker.error) == 'test connection failure'
			                assert app.worker.cleanup_complete
			            app.connect(dict(DEFAULT_SETTINGS, can_context='virtual', controller_id=126))
			            wait(lambda: app.worker.ready_event.is_set())
			    finally:
			        assert app.shutdown(timeout=8)
			''')

	@unittest.skipUnless(importlib.util.find_spec('wx'), 'wxPython is not installed')
	def test_connection_dialog_labels_fit_at_default_and_narrow_sizes(self):
		self.run_script('''\
			import os
			import tempfile
			from types import SimpleNamespace
			from application import Application
			import wx
			with tempfile.TemporaryDirectory() as directory:
			    os.environ['BRS_SETTINGS_PATH'] = os.path.join(directory, 'settings.ini')
			    app = Application(SimpleNamespace(gui=True, profile='main', interactive_connection=True))
			    app.start()
			    try:
			        frame = app.gui._ex
			        assert not frame.connection_dialog.IsShown()
			        frame.on_connection_config(None)
			        dialog = frame.connection_dialog
			        panel = frame.connection_panel
			        assert panel.GetParent() is dialog
			        assert frame.GetSizer().GetItemCount() == 2
			        for size in (None, (640, 400), (500, 400), 'large_font'):
			            if size == 'large_font':
			                font = panel.GetFont()
			                font.SetFractionalPointSize(font.GetFractionalPointSize() * 1.5)
			                for child in panel.GetChildren():
			                    child.SetFont(font)
			                    child.InvalidateBestSize()
			                panel.Layout()
			                size = (500, 400)
			            if size is not None:
			                dialog.SetSize(size)
			                dialog.Layout()
			            wx.GetApp().Yield()
			            assert dialog.GetClientRect().Contains(panel.GetRect()), (size, panel.GetRect())
			            controls = (frame.controller_id_ctrl, frame.transport_ctrl,
			                frame.can_context_ctrl, frame.udp_port_ctrl)
			            assert len({control.GetPosition().x for control in controls}) == 1
			            for control in controls:
			                assert control.GetRect().GetRight() >= panel.GetClientSize().width - panel.FromDIP(5) - 1
			            for child in panel.GetChildren():
			                rect = child.GetRect()
			                assert panel.GetClientRect().Contains(rect), (size, child.GetLabel(), rect, panel.GetClientSize())
			                if isinstance(child, wx.StaticText):
			                    best = child.GetTextExtent(child.GetLabel())
			                    assert rect.width >= best.width and rect.height >= best.height, (size, child.GetLabel(), rect, best)
			    finally:
			        assert app.shutdown()
			''')

	@unittest.skipUnless(importlib.util.find_spec('wx'), 'wxPython is not installed')
	def test_real_wx_dialog_persistence_buttons_and_idle_close(self):
		self.run_script('''\
			import os
			import tempfile
			import threading
			from types import SimpleNamespace
			from application import Application
			from connection_settings import load_settings
			import config
			import wx
			class Worker(threading.Thread):
			    def __init__(self, args, gui, stop):
			        super().__init__()
			        self.args = args
			        self.stop_event = stop
			        self.ready_event = threading.Event()
			        self.error = None
			        self.cleanup_complete = False
			        self._newPreset = None
			        self._scenario_thread = None
			    def run(self):
			        self.ready_event.set()
			        self.stop_event.wait()
			        self.cleanup_complete = True
			with tempfile.TemporaryDirectory() as directory:
			    os.environ['BRS_SETTINGS_PATH'] = os.path.join(directory, 'settings.ini')
			    args = SimpleNamespace(gui=True, profile='main', interactive_connection=True)
			    app = Application(args, worker_factory=Worker)
			    app.start()
			    frame = app.gui._ex
			    try:
			        wx.GetApp().Yield()
			        assert app.worker is None
			        dialog = frame.connection_dialog
			        assert not dialog.IsShown()
			        assert frame.GetMenuBar().GetMenuLabel(1) == 'Config'
			        assert frame.GetMenuBar().IsEnabledTop(1)
			        event = wx.CommandEvent(wx.EVT_MENU.typeId, frame._connection_menu_item.GetId())
			        frame.GetEventHandler().ProcessEvent(event)
			        assert dialog.IsShown()
			        assert frame.connection_panel.IsShownOnScreen()
			        assert frame.connect_button.IsEnabled()
			        assert not frame.disconnect_button.IsEnabled()
			        assert not frame._presets_menu_item.IsEnabled()
			        frame.controller_id_ctrl.SetValue('123')
			        frame.transport_ctrl.SetSelection(1)
			        frame.udp_port_ctrl.SetValue('32000')
			        dialog.Close()
			        assert not dialog.IsShown()
			        assert app.worker is None
			        frame.on_connection_config(None)
			        assert frame.connection_dialog is dialog
			        assert frame.controller_id_ctrl.GetValue() == '123'
			        frame.on_connect(None)
			        assert app.worker.ready_event.wait(2)
			        frame.update_connection()
			        assert not frame.connect_button.IsEnabled()
			        assert frame.disconnect_button.IsEnabled()
			        assert not frame.controller_id_ctrl.IsEnabled()
			        assert frame._presets_menu_item.IsEnabled()
			        worker = app.worker
			        worker.ready_event.clear()
			        frame.update_connection()
			        dialog.Close()
			        assert not dialog.IsShown()
			        assert worker.is_alive() and not app.stop_event.is_set()
			        worker.ready_event.set()
			        frame.on_connection_config(None)
			        assert frame.connection_status.GetLabel() == 'Подключено'
			        close_button = dialog.FindWindow(wx.ID_CLOSE)
			        close_button.GetEventHandler().ProcessEvent(wx.CommandEvent(wx.EVT_BUTTON.typeId, wx.ID_CLOSE))
			        assert not dialog.IsShown()
			        assert app.worker is worker and not app.stop_event.is_set()
			        frame.on_connection_config(None)
			        saved = load_settings(config.ConfigParserInstance(), 'main')
			        assert (saved['controller_id'], saved['transport'], saved['udp_port']) == (123, 'udp', 32000)
			        frame._scenario_status = 'running'
			        frame.update_connection()
			        assert not frame.disconnect_button.IsEnabled()
			        frame.on_disconnect(None)
			        assert not app.stop_event.is_set()
			        frame._scenario_status = 'finished'
			        frame.on_disconnect(None)
			        app.worker.join(2)
			        frame.update_connection()
			        assert frame.connect_button.IsEnabled()
			        assert not frame._scenarios_menu_item.IsEnabled()
			        app.worker.error = RuntimeError('test error')
			        frame.update_connection()
			        assert 'test error' in frame.connection_status.GetLabel()
			        app.request_stop()
			        frame.update_connection()
			        assert app.gui._stopped
			    finally:
			        assert app.shutdown()
			''')

	@unittest.skipUnless(importlib.util.find_spec('wx'), 'wxPython is not installed')
	def test_config_menu_is_disabled_for_cli_sessions(self):
		self.run_script('''\
			import os
			import tempfile
			from gui.frame import guiThread
			with tempfile.TemporaryDirectory() as directory:
			    os.environ['BRS_SETTINGS_PATH'] = os.path.join(directory, 'settings.ini')
			    gui = guiThread()
			    try:
			        frame = gui._ex
			        assert frame.connection_dialog is None
			        assert not frame.GetMenuBar().IsEnabledTop(1)
			        frame.on_connection_config(None)
			        assert frame.connection_dialog is None
			    finally:
			        gui.stop()
			''')


if __name__ == '__main__':
	unittest.main()

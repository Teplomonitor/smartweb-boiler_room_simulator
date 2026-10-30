"""Standalone dashboard for parallel CAN scenario runs (no controller in the GUI)."""

import configparser
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading

import wx

from parallel_can import select_scenarios, validate_contexts
from scenario.scenario import get_scenario_dir


ROOT = Path(__file__).resolve().parents[1]
MAX_CONSOLE_CHARS = 200_000


def can_contexts():
	config = configparser.ConfigParser()
	config.read(ROOT / 'can.ini')
	return [name for name in config.sections() if name.isidentifier()
		and config.get(name, 'interface', fallback='').lower() not in ('', 'virtual')]


def build_command(contexts, scenarios):
	"""Use exactly the same validation and dispatch path as the CLI."""
	validate_contexts(contexts)
	selected = select_scenarios(scenarios)
	if not selected:
		raise ValueError('Select at least one scenario')
	return [sys.executable, '-u', str(ROOT / 'main.py'), '--no-gui',
		'--can-gui-child', '--can-ports', *contexts, '--scenarios', *selected]


def append_console(control, text):
	control.AppendText(text)
	if control.GetLastPosition() > MAX_CONSOLE_CHARS:
		control.Remove(0, control.GetLastPosition() - MAX_CONSOLE_CHARS)


class WorkerConsole(wx.Frame):
	def __init__(self, parent, context, index):
		super().__init__(parent, title=f'CAN: {context}', size=(760, 420))
		self.context = context
		self.index = index
		self.offset = 0
		self.log_path = None
		self.console = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
		self.Bind(wx.EVT_CLOSE, self.on_close)

	def on_close(self, event):
		# Hiding a monitor must not stop a test or destroy its log cursor.
		if self.GetParent().running and event.CanVeto():
			self.Hide()
			event.Veto()
		else:
			event.Skip()

	def read_log(self):
		if self.log_path is None or not self.log_path.is_file():
			return
		with self.log_path.open('rb') as stream:
			stream.seek(self.offset)
			data = stream.read(65536)
			self.offset = stream.tell()
		if data:
			append_console(self.console, data.decode('utf-8', errors='replace'))


class ParallelCanFrame(wx.Frame):
	def __init__(self):
		super().__init__(None, title='Parallel CAN scenarios', size=(900, 720))
		self.process = None
		self.running = False
		self.stopping = False
		self.reader = None
		self.lines = queue.Queue()
		self.monitors = []
		self.run_dir = None
		self.timer = wx.Timer(self)

		panel = wx.Panel(self)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticText(panel, label='CAN contexts (select one or more distinct adapters):'),
			0, wx.ALL, 6)
		self.context_names = can_contexts()
		self.context_list = wx.CheckListBox(panel, choices=self.context_names)
		sizer.Add(self.context_list, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
		sizer.Add(wx.StaticText(panel, label='Scenarios (one, several, or all):'), 0, wx.ALL, 6)
		self.scenario_paths = select_scenarios('all')
		base = get_scenario_dir()
		labels = [os.path.relpath(path, base).replace(os.sep, '/')
			for path in self.scenario_paths]
		self.scenario_list = wx.CheckListBox(panel, choices=labels)
		sizer.Add(self.scenario_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
		buttons = wx.BoxSizer(wx.HORIZONTAL)
		for label, handler in (('Select all', self.select_all),
			('Clear all', self.clear_all), ('Start', self.start),
			('Stop', self.stop), ('Show consoles', self.show_consoles)):
			button = wx.Button(panel, label=label)
			button.Bind(wx.EVT_BUTTON, handler)
			buttons.Add(button, 0, wx.ALL, 4)
			if label == 'Start':
				self.start_button = button
			if label == 'Stop':
				self.stop_button = button
		buttons.AddStretchSpacer()
		sizer.Add(buttons, 0, wx.EXPAND | wx.ALL, 4)
		sizer.Add(wx.StaticText(panel, label='Coordinator / results:'), 0, wx.ALL, 6)
		self.console = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
		sizer.Add(self.console, 1, wx.EXPAND | wx.ALL, 6)
		panel.SetSizer(sizer)
		self.stop_button.Disable()
		self.Bind(wx.EVT_TIMER, self.poll, self.timer)
		self.Bind(wx.EVT_CLOSE, self.on_close)

	def select_all(self, event):
		for index in range(self.scenario_list.GetCount()):
			self.scenario_list.Check(index, True)

	def clear_all(self, event):
		for index in range(self.scenario_list.GetCount()):
			self.scenario_list.Check(index, False)

	def show_consoles(self, event):
		for monitor in self.monitors:
			monitor.Show()
			monitor.Raise()

	def start(self, event):
		if self.running:
			return
		contexts = [name for index, name in enumerate(self.context_names)
			if self.context_list.IsChecked(index)]
		scenarios = [path for index, path in enumerate(self.scenario_paths)
			if self.scenario_list.IsChecked(index)]
		try:
			command = build_command(contexts, scenarios)
			env = os.environ.copy()
			env['PYTHONIOENCODING'] = 'utf-8:backslashreplace'
			process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE,
				stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
				encoding='utf-8', errors='replace', bufsize=1, env=env)
		except (ValueError, OSError) as exc:
			wx.MessageBox(str(exc), 'Cannot start parallel CAN', wx.OK | wx.ICON_ERROR, parent=self)
			return
		self.process = process
		self.running = True
		self.stopping = False
		self.run_dir = None
		self.console.Clear()
		for monitor in self.monitors:
			monitor.Destroy()
		self.monitors = [WorkerConsole(self, context, index)
			for index, context in enumerate(contexts)]
		self.show_consoles(None)
		self.start_button.Disable()
		self.stop_button.Enable()
		self.context_list.Disable()
		self.scenario_list.Disable()
		self.reader = threading.Thread(target=self.read_output, daemon=True)
		self.reader.start()
		self.timer.Start(200)

	def read_output(self):
		try:
			for line in self.process.stdout:
				self.lines.put(line)
		finally:
			self.process.stdout.close()

	def stop(self, event):
		if not self.running or self.stopping:
			return
		self.stopping = True
		self.stop_button.Disable()
		append_console(self.console, 'Stopping workers; waiting for cleanup...\n')
		try:
			self.process.stdin.write('stop\n')
			self.process.stdin.flush()
		except (BrokenPipeError, OSError) as exc:
			append_console(self.console, f'Unable to request stop: {exc}\n')

	def poll(self, event):
		for _ in range(250):
			try:
				line = self.lines.get_nowait()
			except queue.Empty:
				break
			append_console(self.console, line)
			if line.startswith('Parallel CAN run: '):
				self.run_dir = Path(line.removeprefix('Parallel CAN run: ').strip())
				for monitor in self.monitors:
					monitor.log_path = (self.run_dir /
						f'worker_{monitor.index}_{monitor.context}' / 'console.txt')
		for monitor in self.monitors:
			try:
				monitor.read_log()
			except OSError as exc:
				append_console(self.console, f'[{monitor.context}] Cannot read log: {exc}\n')
		if self.process.poll() is not None and not self.reader.is_alive() and self.lines.empty():
			self.timer.Stop()
			self.running = False
			self.process.stdin.close()
			append_console(self.console, f'Finished (exit code {self.process.returncode}). '
				f'Results: {self.run_dir / "results.json" if self.run_dir else "not available"}\n')
			self.start_button.Enable()
			self.stop_button.Disable()
			self.context_list.Enable()
			self.scenario_list.Enable()

	def on_close(self, event):
		if self.running:
			self.stop(None)
			if event.CanVeto():
				wx.MessageBox('Waiting for workers to stop. Close again after cleanup.',
					'Parallel CAN', wx.OK | wx.ICON_INFORMATION, parent=self)
				event.Veto()
				return
		self.timer.Stop()
		for monitor in self.monitors:
			monitor.Destroy()
		self.Destroy()


def main():
	app = wx.App(False)
	frame = ParallelCanFrame()
	frame.Show()
	app.MainLoop()


if __name__ == '__main__':
	main()
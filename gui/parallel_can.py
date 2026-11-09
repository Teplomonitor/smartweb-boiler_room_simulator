"""Standalone dashboard for parallel CAN/UDP scenario runs."""

import configparser
from datetime import datetime, timedelta
import heapq
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time

import wx

from parallel_can import (COORDINATOR_STATE_PREFIX, select_scenarios, validate_contexts,
	validate_udp_ports)
from scenario.metadata import PRESET_LOADING_ESTIMATE_SECONDS, read_scenario_details, scenario_label
from scenario.scenario import get_scenario_dir


ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PATH = ROOT / 'parallel_can_settings.json'
MAX_CONSOLE_CHARS = 200_000
RESULT_STATUS_PRIORITY = {'OK': 0, 'NOT_RUN': 1, 'INTERRUPTED': 2, 'FAIL': 3, 'ERROR': 4}


def scenario_result_statuses(results):
	"""A scenario is OK only when every reported checklist item is OK."""
	statuses = {}
	for result in results:
		path = result.get('scenario')
		status = result.get('result')
		if not isinstance(path, str) or not path or not isinstance(status, str):
			continue
		# An unknown result must not turn a partially successful scenario into OK.
		if status not in RESULT_STATUS_PRIORITY:
			status = 'ERROR'
		previous = statuses.get(path, 'OK')
		if RESULT_STATUS_PRIORITY[status] >= RESULT_STATUS_PRIORITY[previous]:
			statuses[path] = status
	return statuses


def result_counts(results):
	"""Count completed failures separately from interrupted and unassigned tests."""
	counts = {name: 0 for name in ('OK', 'FAIL', 'ERROR', 'INTERRUPTED', 'NOT_RUN')}
	for result in results:
		status = result.get('result')
		if status in counts:
			counts[status] += 1
	return counts


def estimate_remaining(state, estimates, age=0):
	"""Simulate dispatch to currently available workers; unknown durations stay unknown."""
	workers = [worker for worker in state.get('workers', [])
		if worker.get('ready') and not worker.get('retiring')]
	pending = state.get('pending', [])
	if not workers:
		return None
	loads = []
	for worker in workers:
		path = worker.get('scenario')
		if path:
			duration = estimates.get(path)
			if duration is None:
				return None
			loads.append(max(duration * 0.2, duration - worker.get('elapsed', 0) - age))
		else:
			loads.append(0)
	heapq.heapify(loads)
	for path in pending:
		duration = estimates.get(path)
		if duration is None:
			return None
		heapq.heapreplace(loads, loads[0] + duration)
	return max(loads)


def can_contexts():
	config = configparser.ConfigParser()
	config.read(ROOT / 'can.ini')
	return [name for name in config.sections() if name.isidentifier()
		and config.get(name, 'interface', fallback='').lower() not in ('', 'virtual')]


def build_command(contexts, scenarios, udp_ports=None):
	"""Use exactly the same validation and dispatch path as the CLI."""
	ports = validate_udp_ports(udp_ports)
	if contexts:
		validate_contexts(contexts)
	if not contexts and not ports:
		raise ValueError('Select at least one CAN context or UDP port')
	if set(contexts) & {f'udp_{port}' for port in ports}:
		raise ValueError('CAN context conflicts with UDP connection name')
	selected = select_scenarios(scenarios)
	if not selected:
		raise ValueError('Select at least one scenario')
	command = [sys.executable, '-u', str(ROOT / 'main.py'), '--no-gui', '--can-gui-child']
	if contexts:
		command.extend(['--can-ports', *contexts])
	if ports:
		command.extend(['--udp-ports', *(str(port) for port in ports)])
	return [*command, '--scenarios', *selected]


def append_console(control, text):
	control.AppendText(text)
	if control.GetLastPosition() > MAX_CONSOLE_CHARS:
		control.Remove(0, control.GetLastPosition() - MAX_CONSOLE_CHARS)


def load_settings(path):
	try:
		with path.open(encoding='utf-8') as stream:
			settings = json.load(stream)
	except FileNotFoundError:
		return {}
	if not isinstance(settings, dict):
		raise ValueError('Settings must be a JSON object')
	return settings


def save_settings(path, settings):
	"""Replace the previous settings only after the new file is fully written."""
	temp_path = None
	try:
		with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
				prefix=f'.{path.name}.', suffix='.tmp', delete=False) as stream:
			temp_path = Path(stream.name)
			json.dump(settings, stream, ensure_ascii=False, indent=2)
			stream.write('\n')
		os.replace(temp_path, path)
	finally:
		if temp_path is not None:
			temp_path.unlink(missing_ok=True)


class WorkerConsole(wx.Frame):
	def __init__(self, parent, context, index):
		super().__init__(parent, title=f'UDP: {context[4:]}' if context.startswith('udp_')
			else f'CAN: {context}', size=(760, 420))
		self.context = context
		self.index = index
		self.offset = 0
		self.log_path = None
		self.console = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
		self.Bind(wx.EVT_CLOSE, self.on_close)

	def on_close(self, event):
		# Hiding a monitor must not stop a test or destroy its log cursor.
		if event.CanVeto():
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
		super().__init__(None, title='Parallel CAN/UDP scenarios', size=(900, 720))
		self.process = None
		self.running = False
		self.stopping = False
		self.close_requested = False
		self.closing = False
		self.reader = None
		self.lines = queue.Queue()
		self.monitors = []
		self.run_dir = None
		self.run_total = 0
		self.run_estimates = {}
		self.scenario_statuses = {}
		self.run_scenario_keys = set()
		self.state = None
		self.state_received_at = None
		self.timer = wx.Timer(self)

		panel = wx.Panel(self)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(wx.StaticText(panel, label='CAN contexts (select one or more distinct adapters):'),
			0, wx.ALL, 6)
		self.context_names = can_contexts()
		self.context_list = wx.CheckListBox(panel, choices=self.context_names)
		sizer.Add(self.context_list, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
		sizer.Add(wx.StaticText(panel, label='UDP bridge ports (space or comma separated; optional):'),
			0, wx.ALL, 6)
		self.udp_ports_input = wx.TextCtrl(panel)
		sizer.Add(self.udp_ports_input, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
		sizer.Add(wx.StaticText(panel, label='Scenarios (one, several, or all):'), 0, wx.ALL, 6)
		self.scenario_paths = select_scenarios('all')
		base = Path(get_scenario_dir()).resolve()
		self.scenario_keys = {path: Path(path).resolve().relative_to(base).as_posix()
			for path in self.scenario_paths}
		self.scenario_labels = [scenario_label(path, include_path=True, scenario_dir=base)
			for path in self.scenario_paths]
		self.scenario_list = wx.CheckListBox(panel, choices=self.scenario_labels, style=wx.LB_HSCROLL)
		self.scenario_list.SetToolTip('Отметка — результат последнего запуска каждого сценария. '
			'Галочки автоматически не снимаются.')
		sizer.Add(self.scenario_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
		self.scenario_list.Bind(wx.EVT_CHECKLISTBOX, self.update_selection)
		self.selection_label = wx.StaticText(panel, label='')
		sizer.Add(self.selection_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
		buttons = wx.WrapSizer(wx.HORIZONTAL)
		for label, handler in (('Select all', self.select_all),
			('Clear all', self.clear_all), ('Снять галочки с OK', self.clear_ok), ('Start', self.start),
			('Stop', self.stop), ('Show consoles', self.show_consoles)):
			button = wx.Button(panel, label=label)
			button.Bind(wx.EVT_BUTTON, handler)
			buttons.Add(button, 0, wx.ALL, 4)
			if label == 'Start':
				self.start_button = button
			if label == 'Stop':
				self.stop_button = button
			if label == 'Select all':
				self.select_all_button = button
			if label == 'Clear all':
				self.clear_all_button = button
			if label == 'Снять галочки с OK':
				self.clear_ok_button = button
		sizer.Add(buttons, 0, wx.EXPAND | wx.ALL, 4)
		self.progress_label = wx.StaticText(panel, label='Завершено: 0 из 0')
		sizer.Add(self.progress_label, 0, wx.LEFT | wx.RIGHT, 6)
		self.progress_gauge = wx.Gauge(panel, range=1)
		sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.ALL, 6)
		self.eta_label = wx.StaticText(panel, label='Окончание: неизвестно')
		sizer.Add(self.eta_label, 0, wx.LEFT | wx.RIGHT, 6)
		self.summary_label = wx.StaticText(panel, label='')
		sizer.Add(self.summary_label, 0, wx.ALL, 6)
		sizer.Add(wx.StaticText(panel, label='Coordinator / results:'), 0, wx.ALL, 6)
		self.console = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
		sizer.Add(self.console, 1, wx.EXPAND | wx.ALL, 6)
		panel.SetSizer(sizer)
		self.stop_button.Disable()
		self.Bind(wx.EVT_TIMER, self.poll, self.timer)
		self.Bind(wx.EVT_CLOSE, self.on_close)
		self.restore_settings()
		self.refresh_scenario_labels()
		self.update_selection()

	def restore_settings(self):
		try:
			settings = load_settings(SETTINGS_PATH)
		except (OSError, UnicodeError, ValueError) as exc:
			append_console(self.console, f'Cannot load parallel settings: {exc}\n')
			return
		contexts = settings.get('contexts', [])
		if isinstance(contexts, list):
			for index, name in enumerate(self.context_names):
				self.context_list.Check(index, name in contexts)
		ports = settings.get('udp_ports', '')
		if isinstance(ports, str):
			self.udp_ports_input.SetValue(ports)
		scenarios = settings.get('scenarios', [])
		if isinstance(scenarios, list):
			base = Path(get_scenario_dir()).resolve()
			for index, path in enumerate(self.scenario_paths):
				relative = Path(path).resolve().relative_to(base).as_posix()
				self.scenario_list.Check(index, relative in scenarios)
		statuses = settings.get('scenario_statuses', {})
		if isinstance(statuses, dict):
			for key in self.scenario_keys.values():
				status = statuses.get(key)
				if isinstance(status, str) and status in RESULT_STATUS_PRIORITY:
					self.scenario_statuses[key] = status

	def save_settings(self):
		base = Path(get_scenario_dir()).resolve()
		settings = {
			'contexts': [name for index, name in enumerate(self.context_names)
				if self.context_list.IsChecked(index)],
			'udp_ports': self.udp_ports_input.GetValue(),
			'scenarios': [Path(path).resolve().relative_to(base).as_posix()
				for index, path in enumerate(self.scenario_paths)
				if self.scenario_list.IsChecked(index)],
			# Transient states cannot resume after closing the dashboard.
			'scenario_statuses': {key: {'PENDING': 'NOT_RUN', 'RUNNING': 'INTERRUPTED'}.get(status, status)
				for key, status in self.scenario_statuses.items()},
		}
		try:
			save_settings(SETTINGS_PATH, settings)
		except OSError as exc:
			message = f'Cannot save parallel settings: {exc}'
			append_console(self.console, f'{message}\n')
			return message
		return None

	def select_all(self, event):
		for index in range(self.scenario_list.GetCount()):
			self.scenario_list.Check(index, True)
		self.update_selection()

	def clear_all(self, event):
		for index in range(self.scenario_list.GetCount()):
			self.scenario_list.Check(index, False)
		self.update_selection()

	def clear_ok(self, event):
		if self.running:
			return
		for index, path in enumerate(self.scenario_paths):
			if self.scenario_statuses.get(self.scenario_keys[path]) == 'OK':
				self.scenario_list.Check(index, False)
		self.update_selection()

	def refresh_scenario_labels(self):
		for index, path in enumerate(self.scenario_paths):
			status = self.scenario_statuses.get(self.scenario_keys[path])
			label = f'[{status}] {self.scenario_labels[index]}' if status else self.scenario_labels[index]
			if self.scenario_list.GetString(index) != label:
				checked = self.scenario_list.IsChecked(index)
				self.scenario_list.SetString(index, label)
				self.scenario_list.Check(index, checked)
		self.update_selection()

	def update_scenario_statuses(self, results, final=False):
		if self.state and not final:
			for worker in self.state.get('workers', []):
				key = self.scenario_keys.get(worker.get('scenario'))
				if key is not None:
					self.scenario_statuses[key] = 'RUNNING'
		for path, status in scenario_result_statuses(results).items():
			key = self.scenario_keys.get(path)
			if key is not None:
				self.scenario_statuses[key] = status
		if final:
			for key in self.run_scenario_keys:
				status = self.scenario_statuses.get(key)
				if status in ('PENDING', 'RUNNING'):
					self.scenario_statuses[key] = 'INTERRUPTED' if status == 'RUNNING' else 'NOT_RUN'
		self.refresh_scenario_labels()

	def update_selection(self, event=None):
		selected = sum(self.scenario_list.IsChecked(index)
			for index in range(self.scenario_list.GetCount()))
		self.selection_label.SetLabel(f'Выбрано сценариев: {selected}')
		self.clear_ok_button.Enable(not self.running and any(
			self.scenario_list.IsChecked(index)
			and self.scenario_statuses.get(self.scenario_keys[path]) == 'OK'
			for index, path in enumerate(self.scenario_paths)))

	def update_progress(self, final=False, results=None):
		if results is None:
			results = self.state.get('results', []) if self.state else []
		self.update_scenario_statuses(results, final=final)
		counts = result_counts(results)
		completed = counts['OK'] + counts['FAIL'] + counts['ERROR']
		self.progress_gauge.SetRange(max(1, self.run_total))
		self.progress_gauge.SetValue(min(completed, self.run_total))
		self.progress_label.SetLabel(f'Завершено: {completed} из {self.run_total}')
		self.summary_label.SetLabel(f"Успешно: {counts['OK']} | Неудачно: "
			f"{counts['FAIL'] + counts['ERROR']} (FAIL: {counts['FAIL']}, ERROR: {counts['ERROR']})"
			f" | Прервано: {counts['INTERRUPTED']} | Не выполнено: {counts['NOT_RUN']}")
		if final:
			self.eta_label.SetLabel('Проверка завершена' if completed == self.run_total
				else 'Проверка остановлена или завершилась с ошибкой')
		elif self.stopping:
			self.eta_label.SetLabel('Остановка и очистка...')
		elif not self.state or self.state_received_at is None:
			self.eta_label.SetLabel('Окончание: неизвестно')
		else:
			remaining = estimate_remaining(self.state, self.run_estimates,
				time.monotonic() - self.state_received_at)
			if remaining is None:
				self.eta_label.SetLabel('Окончание: неизвестно')
			elif not remaining and completed == self.run_total:
				self.eta_label.SetLabel('Завершение и очистка...')
			else:
				end = datetime.now() + timedelta(seconds=remaining)
				self.eta_label.SetLabel(f'Примерное окончание: {end:%d.%m.%Y %H:%M:%S}')

	def live_monitors(self):
		# wx wrappers can outlive their native windows, including forced closes.
		self.monitors = [monitor for monitor in self.monitors
			if monitor and not monitor.IsBeingDeleted()]
		return self.monitors

	def destroy_monitors(self):
		monitors = self.live_monitors()
		self.monitors = []
		for monitor in monitors:
			monitor.Destroy()

	def show_consoles(self, event):
		if self.closing:
			return
		for monitor in self.live_monitors():
			monitor.Show()
			monitor.Raise()

	def start(self, event):
		if self.running or self.close_requested or self.closing:
			return
		contexts = [name for index, name in enumerate(self.context_names)
			if self.context_list.IsChecked(index)]
		ports = self.udp_ports_input.GetValue().replace(',', ' ').split()
		scenarios = [path for index, path in enumerate(self.scenario_paths)
			if self.scenario_list.IsChecked(index)]
		try:
			command = build_command(contexts, scenarios, ports)
			env = os.environ.copy()
			env['PYTHONIOENCODING'] = 'utf-8:backslashreplace'
			process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE,
				stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
				encoding='utf-8', errors='replace', bufsize=1, env=env)
		except (ValueError, OSError) as exc:
			wx.MessageBox(str(exc), 'Cannot start parallel run', wx.OK | wx.ICON_ERROR, parent=self)
			return
		self.process = process
		self.running = True
		self.stopping = False
		self.run_dir = None
		self.run_total = len(scenarios)
		self.run_estimates = {}
		self.run_scenario_keys = {self.scenario_keys[path] for path in scenarios}
		for key in self.run_scenario_keys:
			self.scenario_statuses[key] = 'PENDING'
		for path in scenarios:
			_, _, estimate = read_scenario_details(path)
			self.run_estimates[path] = (estimate + PRESET_LOADING_ESTIMATE_SECONDS
				if estimate is not None else None)
		self.state = None
		self.state_received_at = None
		self.update_progress()
		self.console.Clear()
		self.save_settings()
		self.destroy_monitors()
		self.monitors = [WorkerConsole(self, context, index)
			for index, context in enumerate([*contexts, *(f'udp_{port}' for port in
				validate_udp_ports(ports))])]
		self.show_consoles(None)
		self.start_button.Disable()
		self.stop_button.Enable()
		self.context_list.Disable()
		self.udp_ports_input.Disable()
		self.scenario_list.Disable()
		self.select_all_button.Disable()
		self.clear_all_button.Disable()
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
		self.update_progress()
		append_console(self.console, 'Stopping workers; waiting for cleanup...\n')
		try:
			self.process.stdin.write('stop\n')
			self.process.stdin.flush()
		except (BrokenPipeError, OSError) as exc:
			append_console(self.console, f'Unable to request stop: {exc}\n')

	def poll(self, event):
		if self.closing:
			return
		for _ in range(250):
			try:
				line = self.lines.get_nowait()
			except queue.Empty:
				break
			if line.startswith(COORDINATOR_STATE_PREFIX):
				try:
					state = json.loads(line[len(COORDINATOR_STATE_PREFIX):])
					if not isinstance(state, dict):
						raise ValueError('State must be an object')
					self.state = state
					self.state_received_at = time.monotonic()
				except (ValueError, TypeError) as exc:
					append_console(self.console, f'Invalid coordinator state: {exc}\n')
				continue
			append_console(self.console, line)
			if line.startswith('Parallel CAN run: '):
				self.run_dir = Path(line.removeprefix('Parallel CAN run: ').strip())
				for monitor in self.live_monitors():
					monitor.log_path = (self.run_dir /
						f'worker_{monitor.index}_{monitor.context}' / 'console.txt')
		for monitor in self.live_monitors():
			try:
				monitor.read_log()
			except OSError as exc:
				append_console(self.console, f'[{monitor.context}] Cannot read log: {exc}\n')
		self.update_progress()
		if self.process.poll() is not None and not self.reader.is_alive() and self.lines.empty():
			self.timer.Stop()
			self.running = False
			self.process.stdin.close()
			results = None
			if self.run_dir:
				try:
					with (self.run_dir / 'results.json').open(encoding='utf-8') as stream:
						results = json.load(stream)
					if not isinstance(results, list) or not all(isinstance(item, dict) for item in results):
						raise ValueError('Results must be a list of objects')
				except (OSError, UnicodeError, ValueError) as exc:
					results = None
					append_console(self.console, f'Cannot read final results: {exc}\n')
			self.update_progress(final=True, results=results)
			if results is None:
				self.eta_label.SetLabel('Итоговый файл недоступен; показаны последние полученные данные')
			append_console(self.console, f'Finished (exit code {self.process.returncode}). '
				f'Results: {self.run_dir / "results.json" if self.run_dir else "not available"}\n')
			append_console(self.console, self.summary_label.GetLabel() + '\n')
			self.start_button.Enable()
			self.stop_button.Disable()
			self.context_list.Enable()
			self.udp_ports_input.Enable()
			self.scenario_list.Enable()
			self.select_all_button.Enable()
			self.clear_all_button.Enable()
			self.save_settings()
			if self.close_requested:
				self.Close()

	def on_close(self, event):
		if self.closing:
			return
		if self.running:
			self.close_requested = True
			self.stop(None)
			if event.CanVeto():
				event.Veto()
				return
		self.closing = True
		error = self.save_settings()
		if error:
			wx.MessageBox(error, 'Parallel CAN/UDP', wx.OK | wx.ICON_WARNING, parent=self)
		self.timer.Stop()
		self.destroy_monitors()
		self.Destroy()


def main():
	app = wx.App(False)
	frame = ParallelCanFrame()
	frame.Show()
	app.MainLoop()


if __name__ == '__main__':
	main()
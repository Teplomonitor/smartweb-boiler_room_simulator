"""Tests for the independent parallel CAN dashboard and its coordinator protocol."""

import io
import json
from pathlib import Path
import queue
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import wx

import parallel_can
from gui.parallel_can import (ParallelCanFrame, WorkerConsole, build_command, can_contexts,
	estimate_remaining, result_counts)
from scenario.metadata import (PRESET_LOADING_ESTIMATE_SECONDS, format_estimated_duration,
	read_scenario_details)


class TestParallelCanGui(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.app = wx.GetApp() or wx.App(False)

	def setUp(self):
		self.settings_dir = tempfile.TemporaryDirectory()
		self.addCleanup(self.settings_dir.cleanup)
		self.settings_path = Path(self.settings_dir.name) / 'settings.json'
		settings_patch = patch('gui.parallel_can.SETTINGS_PATH', self.settings_path)
		settings_patch.start()
		self.addCleanup(settings_patch.stop)

	def test_contexts_exclude_virtual_buses(self):
		self.assertIn('canable0', can_contexts())
		self.assertNotIn('virtual', can_contexts())

	def test_result_counts_separate_failure_from_unfinished(self):
		results = [{'result': value} for value in
			('OK', 'FAIL', 'FAIL', 'ERROR', 'INTERRUPTED', 'NOT_RUN')]
		self.assertEqual(result_counts(results), {'OK': 1, 'FAIL': 2, 'ERROR': 1,
			'INTERRUPTED': 1, 'NOT_RUN': 1})

	def test_remaining_time_accounts_for_busy_parallel_workers(self):
		state = {'workers': [
			{'ready': True, 'scenario': 'a', 'elapsed': 20},
			{'ready': True, 'scenario': None},
			{'ready': True, 'retiring': True, 'scenario': None},
		], 'pending': ['b', 'c']}
		estimates = {'a': 100, 'b': 50, 'c': 70}
		self.assertEqual(estimate_remaining(state, estimates, age=10), 120)
		self.assertIsNone(estimate_remaining(state, {'a': 100, 'b': 50}))
		self.assertIsNone(estimate_remaining({'workers': [], 'pending': ['b']}, estimates))
		self.assertEqual(estimate_remaining({'workers': [state['workers'][0]], 'pending': []},
			estimates, age=100), 20)

	def test_progress_reconciles_final_results_after_stop(self):
		app = wx.GetApp() or wx.App(False)
		frame = ParallelCanFrame()
		try:
			with tempfile.TemporaryDirectory() as temp_dir:
				root = Path(temp_dir)
				results = [{'result': value} for value in
					('OK', 'FAIL', 'ERROR', 'INTERRUPTED', 'NOT_RUN')]
				(root / 'results.json').write_text(json.dumps(results), encoding='utf-8')
				frame.run_total = 5
				frame.run_dir = root
				frame.running = True
				frame.stopping = True
				frame.process = Mock(returncode=2, stdin=io.StringIO())
				frame.process.poll.return_value = 2
				frame.reader = Mock()
				frame.reader.is_alive.return_value = False
				state = {'results': results[:2], 'workers': [], 'pending': []}
				frame.lines.put(parallel_can.COORDINATOR_STATE_PREFIX + json.dumps(state) + '\n')
				frame.poll(None)
				self.assertEqual(frame.progress_label.GetLabel(), 'Завершено: 3 из 5')
				self.assertEqual(frame.progress_gauge.GetValue(), 3)
				self.assertIn('Неудачно: 2 (FAIL: 1, ERROR: 1)', frame.summary_label.GetLabel())
				self.assertIn('Прервано: 1 | Не выполнено: 1', frame.summary_label.GetLabel())
				self.assertNotIn(parallel_can.COORDINATOR_STATE_PREFIX, frame.console.GetValue())
				self.assertFalse(frame.running)
		finally:
			frame.Destroy()
			self.assertIsNotNone(app)

	def test_live_progress_and_missing_final_file(self):
		frame = ParallelCanFrame()
		try:
			frame.run_total = 3
			frame.run_estimates = {'running': 100, 'pending': 50}
			frame.running = True
			frame.process = Mock(stdin=io.StringIO(), returncode=2)
			frame.process.poll.return_value = None
			frame.reader = Mock()
			state = {'results': [{'result': 'FAIL'}], 'pending': ['pending'],
				'workers': [{'ready': True, 'scenario': 'running', 'elapsed': 20}]}
			frame.lines.put(parallel_can.COORDINATOR_STATE_PREFIX + json.dumps(state) + '\n')
			frame.poll(None)
			self.assertEqual(frame.progress_gauge.GetValue(), 1)
			self.assertEqual(frame.progress_label.GetLabel(), 'Завершено: 1 из 3')
			self.assertIn('Примерное окончание:', frame.eta_label.GetLabel())
			frame.process.poll.return_value = 2
			frame.reader.is_alive.return_value = False
			frame.poll(None)
			self.assertIn('Итоговый файл недоступен', frame.eta_label.GetLabel())
			self.assertIn('Неудачно: 1', frame.summary_label.GetLabel())
		finally:
			frame.running = False
			frame.Destroy()

	def test_selection_and_repeat_start_reset_progress(self):
		app = wx.GetApp() or wx.App(False)
		frame = ParallelCanFrame()
		try:
			frame.udp_ports_input.SetValue('31987')
			frame.scenario_list.Check(0, True)
			frame.update_selection()
			self.assertIn('1', frame.selection_label.GetLabel())
			process = Mock()
			process.stdout = io.StringIO('')
			process.stdin = io.StringIO()
			with patch('gui.parallel_can.subprocess.Popen', return_value=process):
				frame.start(None)
			self.assertEqual(frame.progress_label.GetLabel(), 'Завершено: 0 из 1')
			self.assertFalse(frame.select_all_button.IsEnabled())
			frame.state = {'results': [{'result': 'FAIL'}]}
			frame.update_progress()
			self.assertEqual(frame.progress_gauge.GetValue(), 1)
			frame.timer.Stop()
			frame.reader.join()
			frame.running = False
			second = Mock(stdout=io.StringIO(''), stdin=io.StringIO())
			with patch('gui.parallel_can.subprocess.Popen', return_value=second):
				frame.start(None)
			self.assertEqual(frame.progress_gauge.GetValue(), 0)
			self.assertIn('Неудачно: 0', frame.summary_label.GetLabel())
		finally:
			frame.timer.Stop()
			frame.running = False
			frame.Destroy()
			self.assertIsNotNone(app)

	def test_scenario_list_displays_estimate_without_changing_path(self):
		app = wx.GetApp() or wx.App(False)
		frame = ParallelCanFrame()
		try:
			index = next(index for index, path in enumerate(frame.scenario_paths)
				if path.endswith('scenario_heating_circuit_external_priority_5_2_3_3.py'))
			_, _, estimate = read_scenario_details(frame.scenario_paths[index])
			self.assertIn(format_estimated_duration(estimate + PRESET_LOADING_ESTIMATE_SECONDS),
				frame.scenario_list.GetString(index))
			self.assertTrue(frame.scenario_paths[index].endswith('.py'))
		finally:
			frame.timer.Stop()
			frame.Destroy()
			self.assertIsNotNone(app)

	def test_settings_survive_close_and_restore_by_name(self):
		app = wx.GetApp() or wx.App(False)
		frame = ParallelCanFrame()
		try:
			context = frame.context_names[-1]
			scenario = frame.scenario_paths[-1]
			frame.context_list.Check(len(frame.context_names) - 1, True)
			frame.udp_ports_input.SetValue('31987, 31988')
			frame.scenario_list.Check(len(frame.scenario_paths) - 1, True)
			frame.on_close(Mock())
			settings = json.loads(self.settings_path.read_text(encoding='utf-8'))
			settings['contexts'].append('removed_context')
			settings['scenarios'].append('removed_scenario.py')
			self.settings_path.write_text(json.dumps(settings), encoding='utf-8')
			with patch('gui.parallel_can.can_contexts', return_value=list(reversed(frame.context_names))), \
				patch('gui.parallel_can.select_scenarios', return_value=list(reversed(frame.scenario_paths))):
				restored = ParallelCanFrame()
			try:
				self.assertEqual([name for i, name in enumerate(restored.context_names)
					if restored.context_list.IsChecked(i)], [context])
				self.assertEqual(restored.udp_ports_input.GetValue(), '31987, 31988')
				self.assertEqual([path for i, path in enumerate(restored.scenario_paths)
					if restored.scenario_list.IsChecked(i)], [scenario])
			finally:
				restored.Destroy()
		finally:
			self.assertIsNotNone(app)

	def test_bad_settings_do_not_prevent_opening_or_saving(self):
		app = wx.GetApp() or wx.App(False)
		self.settings_path.write_text('{bad json', encoding='utf-8')
		frame = ParallelCanFrame()
		try:
			self.assertIn('Cannot load parallel settings', frame.console.GetValue())
			frame.udp_ports_input.SetValue('invalid port')
			frame.save_settings()
			self.assertEqual(json.loads(self.settings_path.read_text(encoding='utf-8'))['udp_ports'],
				'invalid port')
			with patch('gui.parallel_can.save_settings', side_effect=OSError('read only')):
				frame.save_settings()
			self.assertIn('Cannot save parallel settings: read only', frame.console.GetValue())
		finally:
			frame.Destroy()
			self.assertIsNotNone(app)

	def test_failed_replace_preserves_previous_settings(self):
		app = wx.GetApp() or wx.App(False)
		self.settings_path.write_text('{"udp_ports": "1234"}', encoding='utf-8')
		frame = ParallelCanFrame()
		try:
			frame.udp_ports_input.SetValue('5678')
			with patch('gui.parallel_can.os.replace', side_effect=OSError('read only')):
				frame.save_settings()
			self.assertEqual(json.loads(self.settings_path.read_text(encoding='utf-8'))['udp_ports'],
				'1234')
			self.assertEqual(list(self.settings_path.parent.iterdir()), [self.settings_path])
		finally:
			frame.Destroy()
			self.assertIsNotNone(app)

	def test_close_while_running_waits_before_saving(self):
		app = wx.GetApp() or wx.App(False)
		frame = ParallelCanFrame()
		try:
			frame.running = True
			event = Mock()
			event.CanVeto.return_value = True
			with patch.object(frame, 'stop') as stop, patch('gui.parallel_can.wx.MessageBox'):
				frame.on_close(event)
			stop.assert_called_once_with(None)
			event.Veto.assert_called_once()
			self.assertFalse(self.settings_path.exists())
		finally:
			frame.running = False
			frame.Destroy()
			self.assertIsNotNone(app)

	def test_close_reports_save_failure(self):
		app = wx.GetApp() or wx.App(False)
		frame = ParallelCanFrame()
		with patch('gui.parallel_can.save_settings', side_effect=OSError('read only')), \
			patch('gui.parallel_can.wx.MessageBox') as message_box:
			frame.on_close(Mock())
		self.assertIn('read only', message_box.call_args.args[0])
		self.assertIsNotNone(app)

	def test_invalid_settings_fields_are_ignored(self):
		app = wx.GetApp() or wx.App(False)
		self.settings_path.write_text(json.dumps({'contexts': None, 'udp_ports': [],
			'scenarios': 'all'}), encoding='utf-8')
		frame = ParallelCanFrame()
		try:
			self.assertEqual(frame.udp_ports_input.GetValue(), '')
			self.assertFalse(any(frame.context_list.IsChecked(i)
				for i in range(frame.context_list.GetCount())))
			self.assertFalse(any(frame.scenario_list.IsChecked(i)
				for i in range(frame.scenario_list.GetCount())))
		finally:
			frame.Destroy()
			self.assertIsNotNone(app)

	def test_command_uses_existing_cli_dispatch(self):
		with patch('gui.parallel_can.select_scenarios', return_value=['a.py']):
			command = build_command(['canable0', 'canable1'], ['a.py'])
		self.assertIn('--can-gui-child', command)
		self.assertEqual(command[command.index('--can-ports') + 1:command.index('--scenarios')],
			['canable0', 'canable1'])
		self.assertEqual(command[-1], 'a.py')
		with patch('gui.parallel_can.select_scenarios', return_value=['a.py']):
			one_command = build_command(['canable0'], ['a.py'])
		self.assertEqual(one_command[one_command.index('--can-ports') + 1:
			one_command.index('--scenarios')], ['canable0'])
		with self.assertRaises(ValueError):
			build_command([], ['a.py'])
		with self.assertRaises(ValueError):
			build_command(['ucan', 'ucan'], ['a.py'])
		with patch('gui.parallel_can.select_scenarios', return_value=[]):
			with self.assertRaises(ValueError):
				build_command(['canable0', 'canable1'], [])

	def test_udp_only_and_mixed_commands(self):
		with patch('gui.parallel_can.select_scenarios', return_value=['a.py']):
			udp = build_command([], ['a.py'], ['31987', '31988'])
			self.assertNotIn('--can-ports', udp)
			self.assertEqual(udp[udp.index('--udp-ports') + 1:udp.index('--scenarios')],
				['31987', '31988'])
			mixed = build_command(['canable0'], ['a.py'], ['31987'])
			self.assertEqual(mixed[mixed.index('--can-ports') + 1], 'canable0')
			self.assertEqual(mixed[mixed.index('--udp-ports') + 1], '31987')
			with self.assertRaises(ValueError):
				build_command([], ['a.py'], ['31987', '31987'])

	def test_window_follows_worker_log_and_coordinator_output(self):
		app = wx.GetApp() or wx.App(False)
		frame = ParallelCanFrame()
		try:
			with tempfile.TemporaryDirectory() as temp_dir:
				root = Path(temp_dir)
				log = root / 'worker_0_canable0' / 'console.txt'
				log.parent.mkdir()
				log.write_text('controller ready\n', encoding='utf-8')
				monitor = WorkerConsole(frame, 'canable0', 0)
				frame.monitors = [monitor]
				frame.process = Mock()
				frame.process.poll.return_value = None
				frame.reader = Mock()
				frame.running = True
				frame.lines.put(f'Parallel CAN run: {root}\n')
				frame.poll(None)
				self.assertIn('controller ready', monitor.console.GetValue())
				self.assertIn('Parallel CAN run:', frame.console.GetValue())
				with log.open('a', encoding='utf-8') as stream:
					stream.write('scenario OK\n')
				frame.poll(None)
				self.assertEqual(monitor.console.GetValue(), 'controller ready\nscenario OK\n')
		finally:
			frame.running = False
			frame.Destroy()

	def test_start_with_one_context_opens_one_worker_window(self):
		app = wx.GetApp() or wx.App(False)
		frame = ParallelCanFrame()
		try:
			index = frame.context_names.index('canable0')
			frame.context_list.Check(index, True)
			frame.scenario_list.Check(0, True)
			process = Mock()
			process.stdout = io.StringIO('')
			process.stdin = io.StringIO()
			with patch('gui.parallel_can.subprocess.Popen', return_value=process):
				frame.start(None)
			self.assertEqual([monitor.context for monitor in frame.monitors], ['canable0'])
			self.assertEqual(len(frame.monitors), 1)
		finally:
			frame.timer.Stop()
			frame.running = False
			frame.Destroy()

	def test_udp_only_start_opens_port_monitors(self):
		app = wx.GetApp() or wx.App(False)
		frame = ParallelCanFrame()
		try:
			frame.udp_ports_input.SetValue('31987, 31988')
			frame.scenario_list.Check(0, True)
			process = Mock()
			process.stdout = io.StringIO('')
			process.stdin = io.StringIO()
			with patch('gui.parallel_can.subprocess.Popen', return_value=process) as popen:
				frame.start(None)
			self.assertEqual([monitor.context for monitor in frame.monitors],
				['udp_31987', 'udp_31988'])
			self.assertIn('--udp-ports', popen.call_args.args[0])
			settings = json.loads(self.settings_path.read_text(encoding='utf-8'))
			self.assertEqual(settings['udp_ports'], '31987, 31988')
			self.assertEqual(len(settings['scenarios']), 1)
		finally:
			frame.timer.Stop()
			frame.running = False
			frame.Destroy()

	def test_gui_stop_finishes_results_and_workers(self):
		started = threading.Event()
		stopped = threading.Event()
		assignments = []
		class FakeWorker:
			def __init__(self, context, index, args, run_dir, events):
				self.context = context
				self.current = None
				self.ready = False
				self.retiring = False
				self.process = Mock()
				self.process.poll.return_value = None
				events.put((self, {'type': 'ready'}))

			def send(self, command):
				assignments.append(command['scenario'])
				if len(assignments) == 2:
					started.set()

			def stop(self):
				stopped.set()

			def join(self):
				pass

		class Input:
			def __iter__(self):
				started.wait(5)
				yield 'stop\n'

		args = SimpleNamespace(can_ports=['canable0', 'canable1'], udp=0,
			debug=False, gui=False, scenario='all', can_gui_child=True)
		with tempfile.TemporaryDirectory() as temp_dir:
			run_dir = Path(temp_dir) / 'run'
			run_dir.mkdir()
			output = io.StringIO()
			with patch.object(parallel_can, 'CanWorker', FakeWorker), \
				patch.object(parallel_can, 'select_scenarios', return_value=['a', 'b', 'c']), \
				patch.object(parallel_can, 'validate_contexts'), \
				patch.object(parallel_can, 'resolve_contexts', return_value={}), \
				patch.object(parallel_can.tempfile, 'mkdtemp', return_value=str(run_dir)), \
				patch('sys.stdin', Input()), patch('sys.stdout', output):
				with self.assertRaises(KeyboardInterrupt):
					parallel_can.run_coordinator(args)
			results = json.loads((run_dir / 'results.json').read_text(encoding='utf-8'))
		self.assertTrue(stopped.is_set())
		self.assertEqual(sorted(result['result'] for result in results),
			['INTERRUPTED', 'INTERRUPTED', 'NOT_RUN'])
		states = [json.loads(line[len(parallel_can.COORDINATOR_STATE_PREFIX):])
			for line in output.getvalue().splitlines()
			if line.startswith(parallel_can.COORDINATOR_STATE_PREFIX)]
		self.assertTrue(any(len([worker for worker in state['workers'] if worker['scenario']]) == 2
			for state in states))
		self.assertEqual(states[-1]['results'], results)


if __name__ == '__main__':
	unittest.main()
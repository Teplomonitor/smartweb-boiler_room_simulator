"""Parallel scheduling tests without adapters, GUI, or controller hardware."""

import io
import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import textwrap
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from can.util import load_config
import parallel_can
from main import initArgParser, getProgramLicense
from scenario.scenario import ScenarioThread


class TestParallelCan(unittest.TestCase):
	def test_scenario_initialization_reports_its_phases(self):
		thread = object.__new__(ScenarioThread)
		thread._scenarioList = ['first.py']
		thread._stopScenarioEvent = threading.Event()
		thread.get_scenario_object = Mock(return_value=Mock(get_scenario_title=lambda: 'first'))
		thread.set_gui_status = Mock()
		phases = []
		thread.set_progress_callback(lambda state, path: phases.append((state, path)))
		thread.start_scenario_now('first.py')
		self.assertEqual(phases, [('starting', 'first.py'), ('running', 'first.py')])

	def test_scenario_import_and_construction_have_separate_milestones(self):
		thread = object.__new__(ScenarioThread)
		thread._controllerHost = object()
		thread._simulator = object()
		phases = []
		thread.set_progress_callback(lambda state, path: phases.append((state, path)))
		module = SimpleNamespace(Scenario=Mock(return_value=object()))
		with patch('scenario.scenario.importfile', return_value=module):
			thread.get_scenario_object('first.py')
		self.assertEqual(phases,
			[('importing', 'first.py'), ('constructing', 'first.py')])

	def test_commands_reach_worker_over_real_subprocess_pipes(self):
		script = textwrap.dedent('''\
			import threading
			from types import SimpleNamespace
			import parallel_can
			class ScenarioThread:
			    def set_result_callback(self, callback):
			        self.callback = callback
			    def set_progress_callback(self, callback):
			        self.progress = callback
			    def start_scenario(self, path):
			        self.progress('starting', path)
			        self.progress('running', path)
			        self.callback({'checklistId': 'test', 'result': 'OK', 'duration': 0.1})
			class App:
			    def __init__(self, args):
			        self.stop_event = threading.Event()
			        ready = threading.Event()
			        ready.set()
			        self.worker = SimpleNamespace(ready_event=ready, error=None,
			            _scenario_thread=ScenarioThread(),
			            _controller=SimpleNamespace(get_program_list=lambda: []))
			    def start(self): pass
			    def shutdown(self): return True
			parallel_can.Application = App
			raise SystemExit(parallel_can.run_worker(None))
		''')
		with subprocess.Popen([sys.executable, '-u', '-c', script],
			cwd=Path(__file__).resolve().parents[1], stdin=subprocess.PIPE,
			stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
			process.stdin.write(json.dumps({'type': 'run', 'scenario': 'one.py'}) + '\n')
			process.stdin.flush()
			process.stdin.write(json.dumps({'type': 'stop'}) + '\n')
			process.stdin.flush()
			stdout, stderr = process.communicate(timeout=10)
		self.assertEqual(process.returncode, 0, stderr)
		events = [json.loads(line[len(parallel_can.PROTOCOL_PREFIX):])
			for line in stdout.splitlines()]
		self.assertEqual([event['type'] for event in events],
			['ready', 'progress', 'progress', 'result', 'accepted'])
		self.assertFalse(events[0]['configured'])

	def test_cli_preserves_single_session_and_accepts_parallel_contexts(self):
		args = initArgParser(getProgramLicense(),
			['--no-gui', '--can-ports', 'canable0', 'canable1', '--scenario', 'all'])
		self.assertEqual(args.can_ports, ['canable0', 'canable1'])
		self.assertFalse(args.gui)
		self.assertIsNone(initArgParser(getProgramLicense(), ['--can', 'canable0']).can_ports)

	def test_rejects_virtual_and_duplicate_adapter_mappings(self):
		for contexts in (['virtual', 'canable0'], ['canable0', 'canable0'],
			['default', 'virtual'], ['missing', 'canable0'],
			['canable0', 'ucan'], ['canable1', 'candleLightGsUsb']):
			with self.subTest(contexts=contexts), self.assertRaises(ValueError):
				parallel_can.validate_contexts(contexts)
		parallel_can.validate_contexts(['canable0', 'canable1'])
		parallel_can.validate_contexts(['ucan', 'candleLightGsUsb'])

	def test_named_profiles_are_read_by_python_can(self):
		for context, index in (('ucan', 0), ('candleLightGsUsb', 1)):
			with self.subTest(context=context):
				config = load_config(
					path=Path(__file__).resolve().parents[1] / 'can.ini', context=context)
				self.assertEqual(config['interface'], 'gs_usb')
				self.assertEqual(config['index'], index)
				self.assertEqual(config['bitrate'], 20000)

	def test_only_discovered_scenarios_can_be_selected(self):
		with patch('scenario.scenario.get_scenario_files_list', return_value=['a.py', 'b.py']):
			self.assertEqual(parallel_can.select_scenarios('all'), ['a.py', 'b.py'])
			with self.assertRaises(ValueError):
				parallel_can.select_scenarios('missing.py')

	def test_worker_reports_ready_and_result(self):
		args = SimpleNamespace()
		worker = Mock(error=None)
		worker.ready_event = threading.Event()
		worker.ready_event.set()
		app = Mock(worker=worker)
		app.stop_event = threading.Event()
		output = io.StringIO()
		commands = io.StringIO(json.dumps({'type': 'run', 'scenario': 'one.py'}) + '\n')
		def capture_callback(callback):
			worker._scenario_thread.start_scenario.side_effect = lambda _: callback({
				'checklistId': '1', 'result': 'OK', 'duration': 2.0})
		worker._scenario_thread.set_result_callback.side_effect = capture_callback
		with patch.object(parallel_can, 'Application', return_value=app), \
			patch('sys.stdin', commands), patch('sys.stdout', output):
			self.assertEqual(parallel_can.run_worker(args), 0)
		types = [json.loads(line[len(parallel_can.PROTOCOL_PREFIX):])['type']
			for line in output.getvalue().splitlines()]
		self.assertEqual(types, ['ready', 'result', 'accepted'])
		worker._scenario_thread.start_scenario.assert_called_once_with('one.py')
		app.shutdown.assert_called_once()

	def test_dispatches_next_scenario_to_free_worker(self):
		assignments = []
		class FakeWorker:
			def __init__(self, context, index, args, run_dir, events):
				self.context = context
				self.current = None
				self.ready = False
				self.retiring = False
				self.phase = None
				self.phase_started_at = None
				self.last_notice = None
				self.events = events
				self.process = Mock()
				self.process.poll.return_value = None
				events.put((self, {'type': 'ready'}))

			def send(self, command):
				if command['type'] == 'run':
					assignments.append((self.context, command['scenario']))
					self.events.put((self, {'type': 'result', 'result': 'OK',
						'checklistId': command['scenario'], 'duration': 1.0}))

			def stop(self):
				pass

			def join(self):
				pass

		args = SimpleNamespace(can_ports=['canable0', 'canable1'], udp=0,
			debug=False, gui=False, scenario='all')
		with tempfile.TemporaryDirectory() as temp_dir:
			run_dir = Path(temp_dir) / 'run'
			run_dir.mkdir()
			with patch.object(parallel_can, 'CanWorker', FakeWorker), \
				patch.object(parallel_can, 'select_scenarios', return_value=['a', 'b', 'c']), \
				patch.object(parallel_can, 'validate_contexts'), \
				patch.object(parallel_can.tempfile, 'mkdtemp', return_value=str(run_dir)):
				self.assertEqual(parallel_can.run_coordinator(args), 0)
			self.assertEqual(len(json.loads((run_dir / 'results.json').read_text())), 3)
		self.assertEqual(len(assignments), 3)
		self.assertEqual({name for name, _ in assignments[:2]}, {'canable0', 'canable1'})
		self.assertEqual([path for _, path in assignments], ['a', 'b', 'c'])

	def test_unacknowledged_assignment_times_out_and_remaining_tests_are_not_run(self):
		class SilentWorker:
			def __init__(self, context, index, args, run_dir, events):
				self.context = context
				self.current = None
				self.ready = False
				self.retiring = False
				self.phase = None
				self.phase_started_at = None
				self.last_notice = None
				self.process = Mock()
				self.process.poll.return_value = None
				events.put((self, {'type': 'ready'}))

			def send(self, command):
				pass

			def stop(self):
				pass

			def join(self):
				pass

		args = SimpleNamespace(can_ports=['canable0', 'canable1'], udp=0,
			debug=False, gui=False, scenario='all')
		with tempfile.TemporaryDirectory() as temp_dir:
			run_dir = Path(temp_dir) / 'run'
			run_dir.mkdir()
			with patch.object(parallel_can, 'CanWorker', SilentWorker), \
				patch.object(parallel_can, 'select_scenarios', return_value=['a', 'b', 'c']), \
				patch.object(parallel_can, 'validate_contexts'), \
				patch.object(parallel_can.tempfile, 'mkdtemp', return_value=str(run_dir)), \
				patch.object(parallel_can, 'COMMAND_TIMEOUT', 0):
				self.assertEqual(parallel_can.run_coordinator(args), 2)
			results = json.loads((run_dir / 'results.json').read_text())
		self.assertEqual(sorted(result['result'] for result in results),
			['ERROR', 'ERROR', 'NOT_RUN'])

	def test_each_worker_uses_private_settings_and_logs(self):
		with tempfile.TemporaryDirectory() as temp_dir:
			process = Mock()
			process.stdout = io.StringIO('')
			process.stdin = io.StringIO()
			process.poll.return_value = None
			process.wait.return_value = 0
			with patch.object(parallel_can.subprocess, 'Popen', return_value=process) as popen:
				worker = parallel_can.CanWorker('canable0', 0,
					SimpleNamespace(id=0, profile='main', preset=None),
					Path(temp_dir), queue.Queue())
				worker.stop()
				worker.join()
				self.assertFalse(worker.reader.daemon)
				self.assertFalse(worker.reader.is_alive())
				self.assertTrue(process.stdin.closed)
				env = popen.call_args.kwargs['env']
				self.assertTrue(Path(env['BRS_SETTINGS_PATH']).is_file())
				self.assertEqual(Path(env['BRS_LOG_ROOT']).parent, worker.log_dir)
				self.assertIn('--no-gui', popen.call_args.args[0])
				self.assertEqual(env['PYTHONIOENCODING'], 'utf-8:backslashreplace')
				self.assertEqual(popen.call_args.kwargs['errors'], 'replace')

	def test_bad_console_encoding_does_not_hide_worker_events(self):
		script = "import sys; sys.stdout.buffer.write(b'\\xcd\\n@@BRS_CAN@@{\"type\":\"ready\"}\\n'); sys.stdout.buffer.flush()"
		spawn = subprocess.Popen
		with tempfile.TemporaryDirectory() as temp_dir:
			events = queue.Queue()
			with patch.object(parallel_can.subprocess, 'Popen', side_effect=lambda _command, **kwargs:
				spawn([sys.executable, '-u', '-c', script], **kwargs)):
				worker = parallel_can.CanWorker('ucan', 0,
					SimpleNamespace(id=0, profile='main', preset=None), Path(temp_dir), events)
				worker.join()
			self.assertEqual(worker.process.returncode, 0)
			self.assertEqual(events.get_nowait()[1]['type'], 'ready')
			self.assertEqual(events.get_nowait()[1]['type'], 'exit')
			self.assertIn('\ufffd', (worker.log_dir / 'console.txt').read_text(encoding='utf-8'))


if __name__ == '__main__':
	unittest.main()

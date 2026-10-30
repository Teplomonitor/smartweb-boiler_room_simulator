"""Headless CAN scenario coordinator. Each CAN context has its own process."""

import configparser
import json
import os
from pathlib import Path
import queue
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
import time

from application import Application


PROTOCOL_PREFIX = '@@BRS_CAN@@'
STARTUP_TIMEOUT = 180
SHUTDOWN_TIMEOUT = 70
COMMAND_TIMEOUT = 15
SCENARIO_INIT_TIMEOUT = 10 * 60
PROGRESS_INTERVAL = 60


def send_event(data):
	print(PROTOCOL_PREFIX + json.dumps(data, ensure_ascii=False), flush=True)


def run_worker(args):
	"""Run one controller session and accept one scenario at a time on stdin."""
	commands = queue.Queue()

	def read_commands():
		for line in sys.stdin:
			try:
				commands.put(json.loads(line))
			except json.JSONDecodeError:
				commands.put({'type': 'invalid'})
		commands.put({'type': 'stop'})

	reader = threading.Thread(target=read_commands, daemon=True)
	reader.start()
	app = Application(args)
	try:
		app.start()
		while not app.stop_event.is_set() and not app.worker.ready_event.wait(0.2):
			pass
		if app.stop_event.is_set():
			send_event({'type': 'error', 'error': repr(app.worker.error)})
			return 2
		app.worker._scenario_thread.set_result_callback(
			lambda result: send_event({'type': 'result', **result}))
		app.worker._scenario_thread.set_progress_callback(
			lambda state, path: send_event({'type': 'progress', 'state': state,
				'scenario': path}))
		send_event({'type': 'ready', 'configured': bool(
			app.worker._controller.get_program_list())})
		while not app.stop_event.is_set():
			try:
				command = commands.get(timeout=0.2)
			except queue.Empty:
				continue
			if command.get('type') == 'stop':
				break
			if command.get('type') == 'run':
				app.worker._scenario_thread.start_scenario(command['scenario'])
				send_event({'type': 'accepted', 'scenario': command['scenario']})
			else:
				send_event({'type': 'error', 'error': 'Invalid worker command'})
		return 0 if app.worker.error is None else 2
	finally:
		if not app.shutdown():
			send_event({'type': 'error', 'error': 'Worker shutdown timed out'})


class CanWorker:
	def __init__(self, context, index, args, run_dir, events):
		self.context = context
		self.current = None
		self.ready = False
		self.retiring = False
		self.phase = None
		self.phase_started_at = None
		self.last_notice = None
		self.events = events
		self.log_dir = run_dir / f'worker_{index}_{context}'
		self.log_dir.mkdir()
		settings = self.log_dir / 'settings.ini'
		source = Path(__file__).with_name('settings.ini')
		if source.is_file():
			shutil.copyfile(source, settings)
		env = os.environ.copy()
		env['BRS_SETTINGS_PATH'] = str(settings)
		env['BRS_LOG_ROOT'] = str(self.log_dir / 'log')
		env['PYTHONIOENCODING'] = 'utf-8:backslashreplace'
		command = [sys.executable, '-u', str(Path(__file__).with_name('main.py')),
			'--no-gui', '--can-worker', '--can', context, '--id', str(args.id),
			'--profile', args.profile]
		if args.preset:
			command.extend(['--preset', args.preset])
		self.log = (self.log_dir / 'console.txt').open('w', encoding='utf-8')
		try:
			self.process = subprocess.Popen(command, cwd=Path(__file__).parent,
				stdin=subprocess.PIPE, stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
				bufsize=1, env=env)
		except BaseException:
			self.log.close()
			raise
		self.reader = threading.Thread(target=self._read_output)
		self.reader.start()

	def _read_output(self):
		try:
			for line in self.process.stdout:
				self.log.write(line)
				self.log.flush()
				if line.startswith(PROTOCOL_PREFIX):
					try:
						self.events.put((self, json.loads(line[len(PROTOCOL_PREFIX):])))
					except json.JSONDecodeError:
						self.events.put((self, {'type': 'error', 'error': 'Malformed worker event'}))
		except Exception as exc:
			self.events.put((self, {'type': 'error', 'error': f'Worker output reader failed: {exc!r}'}))
		finally:
			self.events.put((self, {'type': 'exit', 'code': self.process.wait()}))
			self.log.close()

	def send(self, command):
		self.process.stdin.write(json.dumps(command) + '\n')
		self.process.stdin.flush()

	def stop(self):
		if self.process.poll() is not None:
			return
		try:
			self.send({'type': 'stop'})
		except (BrokenPipeError, OSError):
			pass
		finally:
			if self.process.stdin:
				self.process.stdin.close()

	def join(self):
		try:
			self.process.wait(timeout=SHUTDOWN_TIMEOUT)
		except subprocess.TimeoutExpired:
			self.process.kill()
			self.process.wait()
		self.reader.join(timeout=5)
		if self.reader.is_alive():
			self.process.stdout.close()
			self.reader.join()
		if self.process.stdin and not self.process.stdin.closed:
			self.process.stdin.close()


def select_scenarios(selection):
	from scenario.scenario import get_scenario_files_list
	paths = get_scenario_files_list()
	if selection in ('none', 'all'):
		return paths
	requested = selection if isinstance(selection, (list, tuple)) else [selection]
	selected = [str(Path(path).resolve()) for path in requested]
	if len(set(selected)) != len(selected):
		raise ValueError('Scenario paths must be distinct')
	for path in selected:
		if path not in paths:
			raise ValueError(f'Scenario not found: {path}')
	return selected


def validate_contexts(contexts):
	if not contexts or len(set(contexts)) != len(contexts):
		raise ValueError('Specify one or more distinct CAN configuration contexts')
	config = configparser.ConfigParser()
	config.read(Path(__file__).with_name('can.ini'))
	addresses = set()
	for context in contexts:
		if context not in config.sections() or not context.isidentifier():
			raise ValueError(f'Unknown or unsafe CAN context in can.ini: {context}')
		interface = config.get(context, 'interface', fallback='').lower()
		if not interface or interface == 'virtual':
			raise ValueError(f'Parallel CAN requires a physical bus: {context}')
		if interface == 'gs_usb' and config.has_option(context, 'index'):
			address = (interface, config.get(context, 'index'))
		else:
			address = (interface, config.get(context, 'channel', fallback=''),
				config.get(context, 'bus', fallback=''),
				config.get(context, 'address', fallback=''))
		if address in addresses:
			raise ValueError(f'CAN contexts refer to the same adapter: {context}')
		addresses.add(address)


def run_coordinator(args):
	"""Dispatch the next test to the next free controller; never retry implicitly."""
	stop_requested = threading.Event()
	if getattr(args, 'can_gui_child', False):
		def listen_for_stop():
			for line in sys.stdin:
				if line.strip() == 'stop':
					stop_requested.set()
					break
		threading.Thread(target=listen_for_stop, daemon=True).start()
	contexts = args.can_ports
	validate_contexts(contexts)
	if args.udp or args.debug:
		raise ValueError('Parallel CAN mode does not support --udp or --debug')
	if args.gui:
		raise ValueError('Parallel CAN mode requires --no-gui')
	if getattr(args, 'scenarios', None) and args.scenario != 'none':
		raise ValueError('Use either --scenarios or --scenario, not both')
	from collections import deque
	pending = deque(select_scenarios(getattr(args, 'scenarios', None) or args.scenario))
	if not pending:
		raise ValueError('No scenarios found')
	root = Path(__file__).with_name('log')
	root.mkdir(exist_ok=True)
	run_dir = Path(tempfile.mkdtemp(prefix='parallel_can_', dir=root))
	print(f'Parallel CAN run: {run_dir}', flush=True)
	events = queue.Queue()
	workers = []
	results = []
	start = time.monotonic()
	try:
		for index, context in enumerate(contexts):
			workers.append(CanWorker(context, index, args, run_dir, events))
		while pending or any(worker.current for worker in workers):
			if stop_requested.is_set():
				raise KeyboardInterrupt
			try:
				worker, event = events.get(timeout=0.2)
			except queue.Empty:
				if workers and all(w.retiring or w.process.poll() is not None for w in workers):
					break
				now = time.monotonic()
				for w in workers:
					if not w.ready and not w.retiring and w.process.poll() is None and now - start > STARTUP_TIMEOUT:
						print(f'[{w.context}] startup timed out', flush=True)
						w.retiring = True
						w.process.kill()
					if w.current and not w.retiring:
						elapsed = now - w.phase_started_at
						limit = COMMAND_TIMEOUT if w.phase == 'sent' else SCENARIO_INIT_TIMEOUT if w.phase in ('accepted', 'starting', 'importing', 'constructing') else None
						if limit is not None and elapsed > limit:
							message = f'{w.phase} timed out after {elapsed:.0f}s'
							print(f'[{w.context}] {message}', flush=True)
							results.append({'can': w.context, 'scenario': w.current,
								'result': 'ERROR', 'error': message})
							w.current = None
							w.retiring = True
							w.ready = False
						elif now - w.last_notice >= PROGRESS_INTERVAL:
							print(f'[{w.context}] {w.phase}: {Path(w.current).name} ({now - w.phase_started_at:.0f}s in phase)', flush=True)
							w.last_notice = now
				continue
			if event['type'] == 'ready':
				worker.ready = True
				print(f'[{worker.context}] controller connected', flush=True)
				if not event.get('configured', True):
					print(f'[{worker.context}] startup preset did not match; scenario may load its own preset', flush=True)
			elif event['type'] in ('accepted', 'progress') and worker.current and event.get('scenario') == worker.current:
				worker.phase = event.get('state', 'accepted')
				worker.phase_started_at = time.monotonic()
				worker.last_notice = worker.phase_started_at
				print(f'[{worker.context}] {worker.phase}: {Path(worker.current).name}', flush=True)
			elif event['type'] == 'result' and worker.current:
				result = {'can': worker.context, 'scenario': worker.current, **event}
				results.append(result)
				print(f"[{worker.context}] {event['result']} {event['checklistId']} ({event['duration']:.1f}s)", flush=True)
				worker.current = None
			elif event['type'] == 'exit':
				worker.ready = False
				worker.retiring = True
				if worker.current:
					results.append({'can': worker.context, 'scenario': worker.current,
						'result': 'ERROR', 'error': f"Worker exited ({event['code']})"})
					worker.current = None
				print(f"[{worker.context}] worker exited ({event['code']})", flush=True)
			elif event['type'] == 'error':
				print(f"[{worker.context}] {event['error']}", flush=True)
				if event['error'].startswith('Worker output reader failed:'):
					worker.retiring = True
					worker.ready = False
					if worker.current:
						results.append({'can': worker.context, 'scenario': worker.current,
							'result': 'ERROR', 'error': event['error']})
						worker.current = None
					worker.stop()
			for free in workers:
				if free.ready and not free.retiring and free.current is None and pending:
					path = pending.popleft()
					free.current = path
					free.phase = 'sent'
					free.phase_started_at = time.monotonic()
					free.last_notice = free.phase_started_at
					print(f'[{free.context}] starting {Path(path).name}', flush=True)
					try:
						free.send({'type': 'run', 'scenario': path})
					except (BrokenPipeError, OSError) as exc:
						free.ready = False
						results.append({'can': free.context, 'scenario': path,
							'result': 'ERROR', 'error': repr(exc)})
						free.current = None
		unassigned = list(pending)
		for path in unassigned:
			results.append({'scenario': path, 'result': 'NOT_RUN'})
		if unassigned:
			print(f'{len(unassigned)} scenarios not run: no controllers available', flush=True)
		return 0 if results and all(r['result'] == 'OK' for r in results) else 2
	except KeyboardInterrupt:
		for worker in workers:
			if worker.current:
				results.append({'can': worker.context, 'scenario': worker.current,
					'result': 'INTERRUPTED'})
		for path in pending:
			results.append({'scenario': path, 'result': 'NOT_RUN'})
		raise
	except Exception:
		for worker in workers:
			if worker.current:
				results.append({'can': worker.context, 'scenario': worker.current,
					'result': 'ERROR', 'error': 'Coordinator failed'})
		for path in pending:
			results.append({'scenario': path, 'result': 'NOT_RUN'})
		raise
	finally:
		# A second Ctrl+C must not abandon non-daemon pipe readers mid-shutdown.
		previous_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
		try:
			print('Stopping CAN workers and writing results; please wait...', flush=True)
			for worker in workers:
				worker.stop()
			for worker in workers:
				worker.join()
		finally:
			(run_dir / 'results.json').write_text(
				json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
			signal.signal(signal.SIGINT, previous_handler)

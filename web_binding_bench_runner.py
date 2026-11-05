"""One isolated bench session per process. No GUI imports and no power switching."""

import argparse
import json
from pathlib import Path
import sys
import threading
import time

from web_binding_bench import ROOT, load_settings, preflight, selected_scenarios, validate_settings

EVENT_PREFIX = 'BRS_BENCH_EVENT '
STARTUP_TIMEOUT = 90
SHUTDOWN_TIMEOUT = 60


def emit(event, **fields):
	print(EVENT_PREFIX + json.dumps(dict(fields, event=event), ensure_ascii=False), flush=True)


def listen_for_stop(stopped):
	for line in sys.stdin:
		if line.strip() == 'stop':
			stopped.set()
			return
	# A vanished dashboard is a stop request, never permission to continue mutations.
	stopped.set()


def run_session(profile_path, check_only, confirmed, stopped):
	settings = validate_settings(load_settings(profile_path), require_ready=True)
	paths = [] if check_only else selected_scenarios(settings)
	if not check_only and not confirmed:
		raise ValueError('Destructive bench tests require --confirm-bench')
	if stopped.is_set():
		return 130
	# Import main first: the application deliberately retains this import order.
	import main
	from application import Application
	from smartnet.mapping_client import MappingCanClient
	args = main.initArgParser('', ['--no-gui', '--web-bench', str(profile_path)] +
		(['--confirm-web-bench'] if confirmed else []))
	application = Application(args)
	completed = threading.Event()
	seen = set()
	result_lock = threading.Lock()
	failed = threading.Event()
	def report(result):
		key = (result['checklistId'], result['result'], result['duration'])
		with result_lock:
			if key not in seen:
				seen.add(key)
				if result['result'] != 'OK':
					failed.set()
				emit('result', **result)
	def final_result(result):
		report(result)
		completed.set()
	def progress(stage, value):
		path = Path(value).resolve().relative_to(ROOT).as_posix() if isinstance(value, str) else None
		emit('progress', message=f'{stage}: {path or "выбранные сценарии"}', path=path, stage=stage)
	try:
		emit('starting', message='Подключение к стенду (без загрузки стартового пресета)…')
		application.start()
		deadline = time.monotonic() + STARTUP_TIMEOUT
		while not application.worker.ready_event.wait(0.1):
			if stopped.is_set():
				return 130
			if application.stop_event.is_set() or not application.worker.is_alive():
				raise RuntimeError('Application stopped before bench initialization')
			if time.monotonic() >= deadline:
				raise TimeoutError('Bench initialization timed out')
		worker = application.worker
		preflight(settings, MappingCanClient(), worker.web_client, cancelled=stopped.is_set)
		if stopped.is_set():
			return 130
		if check_only:
			emit('checked', message='HTTP/CAN доступны; разводка и управление питанием не проверялись.')
			return 0
		thread = worker._scenario_thread
		thread.set_result_callback(final_result)
		thread.set_progress_callback(progress)
		thread.start_scenario(paths)
		while not completed.wait(0.1):
			for result in list(thread._scenarioResultList):
				report(result)
			if stopped.is_set():
				emit('stopping', message='Остановка сценария и очистка…')
				return 130
			if application.stop_event.is_set() or not worker.is_alive() or not thread.is_alive():
				raise RuntimeError('Bench worker stopped unexpectedly')
		for result in list(thread._scenarioResultList):
			report(result)
		return 1 if failed.is_set() else 0
	except Exception:
		if stopped.is_set():
			return 130
		raise
	finally:
		if not application.shutdown(timeout=SHUTDOWN_TIMEOUT):
			raise RuntimeError('Application cleanup timed out; inspect the bench before continuing')


def main(argv=None):
	if hasattr(sys.stdout, 'reconfigure'):
		sys.stdout.reconfigure(encoding='utf-8', errors='replace')
		sys.stderr.reconfigure(encoding='utf-8', errors='replace')
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--profile', required=True)
	mode = parser.add_mutually_exclusive_group(required=True)
	mode.add_argument('--check', action='store_true')
	mode.add_argument('--run', action='store_true')
	parser.add_argument('--confirm-bench', action='store_true')
	args = parser.parse_args(argv)
	stopped = threading.Event()
	threading.Thread(target=listen_for_stop, args=(stopped,), daemon=True).start()
	try:
		return run_session(args.profile, args.check, args.confirm_bench, stopped)
	except KeyboardInterrupt:
		return 130
	except Exception as error:
		# Do not serialize profile contents, HTTP request bodies or authentication data.
		emit('error', message=f'Ошибка стенда ({type(error).__name__}): {error}')
		return 1


if __name__ == '__main__':
	raise SystemExit(main())
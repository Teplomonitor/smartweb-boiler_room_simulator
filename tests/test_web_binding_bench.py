import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import web_binding_bench as bench


def ready_settings():
	settings = bench.default_settings()
	settings['devices'] = dict(zip(bench.ROLES, (7, 8, 20, 21)))
	settings['web']['url'] = 'http://127.0.0.1:8080'
	settings['power']['relay'] = 8
	settings['sensors'] = [dict(device=role, channel=1, expected=value, tolerance=2)
		for role, value in (('dut_controller', 20), ('dut_extension', 30))]
	settings['feedback'] = [dict(output_device=source, relay=1, input_device=observer,
		sensor=1, closed_when_on=True) for source, observer in (
		('dut_controller', 'aux_controller'), ('dut_extension', 'aux_extension'))]
	settings['scenarios'] = ['scenario/list/web/scenario_web_input_9_1_1.py']
	return settings


class ProfileTests(unittest.TestCase):
	def test_draft_and_ready_are_distinct(self):
		bench.validate_settings(bench.default_settings())
		with self.assertRaises(ValueError):
			bench.validate_settings(bench.default_settings(), require_ready=True)
		bench.validate_settings(ready_settings(), require_ready=True)

	def test_ready_requires_resistor_inputs_and_feedback(self):
		for key in ('sensors', 'feedback'):
			settings = ready_settings()
			settings[key] = []
			with self.assertRaises(ValueError):
				bench.validate_settings(settings, require_ready=True)

	def test_rejects_bad_ids_types_and_parent_relationships(self):
		for value in (True, '7', -1, 256, 20):
			settings = ready_settings()
			settings['devices']['dut_controller'] = value
			with self.subTest(value=value), self.assertRaises(ValueError):
				bench.validate_settings(settings, require_ready=True)
		settings = ready_settings()
		settings['devices'].update(dut_controller=255, dut_extension=1)
		bench.validate_settings(settings, require_ready=True)

	def test_reserved_relay_input_conflicts_and_invalid_polarity(self):
		for change in ('reserved', 'input_conflict', 'output_duplicate', 'polarity', 'channel_zero'):
			settings = ready_settings()
			if change == 'reserved':
				settings['feedback'][0].update(output_device='aux_controller', relay=8)
			elif change == 'input_conflict':
				settings['feedback'][0].update(input_device='dut_controller', sensor=1)
			elif change == 'output_duplicate':
				settings['feedback'].append(copy.deepcopy(settings['feedback'][0]))
			elif change == 'polarity':
				settings['feedback'][0]['closed_when_on'] = 1
			else:
				settings['sensors'][0]['channel'] = 0
			with self.subTest(change=change), self.assertRaises(ValueError):
				bench.validate_settings(settings)

	def test_bad_urls_and_nonfinite_numbers(self):
		for url in ('http://user:pass@localhost', 'http://localhost/rest.php', 'ftp://localhost'):
			settings = ready_settings()
			settings['web']['url'] = url
			with self.assertRaises(ValueError):
				bench.validate_settings(settings)
		for value in (float('nan'), float('inf'), True):
			settings = ready_settings()
			settings['sensors'][0]['expected'] = value
			with self.assertRaises(ValueError):
				bench.validate_settings(settings)

	def test_round_trip_credentials_and_atomic_failure(self):
		settings = ready_settings()
		settings['web']['password'] = 'test-only-password'
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / 'settings.json'
			bench.save_settings(settings, path)
			self.assertEqual(bench.load_settings(path), settings)
			before = path.read_bytes()
			with patch('web_binding_bench.os.replace', side_effect=OSError('denied')):
				with self.assertRaises(OSError):
					bench.save_settings(settings, path)
			self.assertEqual(path.read_bytes(), before)
			self.assertEqual(list(Path(directory).iterdir()), [path])
			path.write_text('{broken', encoding='utf-8')
			with self.assertRaises(ValueError):
				bench.load_settings(path)
			self.assertEqual(path.read_text(encoding='utf-8'), '{broken')

	def test_version_and_unknown_selection_are_rejected(self):
		settings = ready_settings()
		settings['version'] = 2
		with self.assertRaises(ValueError):
			bench.validate_settings(settings)
		settings = ready_settings()
		self.assertEqual(len(bench.selected_scenarios(settings)), 1)
		for paths in ([], ['../../other.py'], [settings['scenarios'][0]] * 2):
			settings['scenarios'] = paths
			with self.assertRaises(ValueError):
				bench.selected_scenarios(settings)

	def test_preflight_is_read_only_and_checks_all_devices(self):
		settings, can, web = ready_settings(), Mock(), Mock()
		can.read_controller_type.side_effect = (10, 11, 10, 11)
		can.read_channel_counts.return_value = (6, 8)
		web.config.return_value = {'controllers': [{'id': value} for value in settings['devices'].values()]}
		before = copy.deepcopy(settings)
		self.assertEqual(bench.preflight(settings, can, web, log=Mock()), before)
		self.assertEqual(settings, before)
		self.assertEqual(can.read_channel_counts.call_count, 4)
		self.assertEqual(set(name for name, _, _ in can.mock_calls), {'read_controller_type', 'read_channel_counts'})
		self.assertEqual(set(name for name, _, _ in web.mock_calls), {'login', 'config', 'logout'})

	def test_preflight_rejects_wrong_extension_missing_http_and_small_counts(self):
		for failure in ('extension', 'http', 'count', 'cancel'):
			can, web = Mock(), Mock()
			can.read_controller_type.side_effect = (10, 99 if failure == 'extension' else 11, 10, 11)
			can.read_channel_counts.return_value = (0, 0) if failure == 'count' else (6, 8)
			web.config.return_value = {'controllers': []}
			with self.subTest(failure=failure), self.assertRaises((ValueError, RuntimeError)):
				bench.preflight(ready_settings(), can, web, log=Mock(), cancelled=lambda: failure == 'cancel')
			if failure == 'http':
				web.logout.assert_called_once()

	def test_cli_derives_transport_and_requires_confirmation(self):
		from main import initArgParser
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / 'bench.json'
			settings = ready_settings()
			bench.save_settings(settings, path)
			options = ['--no-gui', '--web-bench', str(path)]
			args = initArgParser('', options)
			self.assertEqual(args.id, 7)
			self.assertEqual(args.udp, 31987)
			self.assertEqual(args.can, 'virtual')
			self.assertEqual(args.bench_settings['web'], settings['web'])
			for extra in (['--scenario', 'all'], ['--preset', 'web_bindings'], ['--id', '20'],
					['--confirm-web-bench', '--scenario', 'all'], ['--scenarios', 'unrelated.py']):
				with patch('sys.stderr'), self.assertRaises(SystemExit):
					initArgParser('', options + extra)
			with patch('mainThread.config.ConfigParserInstance') as config:
				from mainThread import ApplicationWorker
				worker = ApplicationWorker(args, None, threading.Event())
				self.assertEqual(worker._programPresetList, [])
				self.assertIsNone(worker._newPreset)
				config.return_value.getParameterValue.assert_not_called()
				self.assertEqual(worker.web_client._password, settings['web']['password'])

	def test_controller_type_read_uses_live_protocol(self):
		from smartnet.constants import ControllerFunction, ProgramType
		from smartnet.mapping_client import MappingCanClient
		client = MappingCanClient()
		with patch.object(client, '_exchange', return_value=[11]) as exchange:
			self.assertEqual(client.read_controller_type(8), 11)
			exchange.assert_called_once_with(ProgramType.CONTROLLER, 8,
				ControllerFunction.GET_CONTROLLER_TYPE, [], 1)

	def test_stop_request_and_dashboard_disconnection(self):
		from io import StringIO
		from web_binding_bench_runner import listen_for_stop
		for content in ('stop\n', ''):
			event = threading.Event()
			with patch('sys.stdin', StringIO(content)):
				listen_for_stop(event)
			self.assertTrue(event.is_set())


class WorkerTests(unittest.TestCase):
	def test_check_run_failure_and_cancellation_cleanup(self):
		from web_binding_bench_runner import run_session
		for mode in ('check', 'run', 'failure', 'offline', 'cancel'):
			with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
				path = Path(directory) / 'settings.json'
				bench.save_settings(ready_settings(), path)
				stopped = threading.Event()
				thread = Mock()
				thread._scenarioResultList = []
				result_callback = []
				thread.set_result_callback.side_effect = result_callback.append
				def start(paths):
					result = {'checklistId': '9.1.1', 'result': 'FAIL' if mode == 'failure' else 'OK', 'duration': 1}
					thread._scenarioResultList.append(result)
					result_callback[0](result)
				thread.start_scenario.side_effect = start
				worker = Mock()
				worker._scenario_thread = thread
				worker.ready_event = threading.Event()
				worker.ready_event.set()
				app = Mock(worker=worker)
				app.stop_event = threading.Event()
				app.shutdown.return_value = True
				def check(*args, **kwargs):
					if mode == 'offline':
						raise ValueError('offline')
					if mode == 'cancel':
						stopped.set()
				with patch('application.Application', return_value=app), \
					patch('web_binding_bench_runner.preflight', side_effect=check), \
					patch('web_binding_bench_runner.emit') as emit:
					if mode == 'offline':
						with self.assertRaisesRegex(ValueError, 'offline'):
							run_session(path, False, True, stopped)
					else:
						code = run_session(path, mode == 'check', True, stopped)
						self.assertEqual(code, {'failure': 1, 'cancel': 130}.get(mode, 0))
					if mode in ('check', 'offline', 'cancel'):
						thread.start_scenario.assert_not_called()
					else:
						self.assertEqual(sum(call.args[0] == 'result' for call in emit.call_args_list), 1)
					app.shutdown.assert_called_once()
					app.start.assert_called_once()

	def test_unconfirmed_run_does_not_start_application(self):
		from web_binding_bench_runner import run_session
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / 'settings.json'
			bench.save_settings(ready_settings(), path)
			with patch('application.Application') as application, self.assertRaises(ValueError):
				run_session(path, False, False, threading.Event())
			application.assert_not_called()


class GuiSmokeTests(unittest.TestCase):
	def test_window_tables_schema_and_save_without_network(self):
		import tkinter as tk
		from gui.web_bindings import BenchFrame
		try:
			root = tk.Tk()
		except tk.TclError as error:
			self.skipTest(f'No GUI display: {error}')
		self.addCleanup(root.destroy)
		root.withdraw()
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / 'settings.json'
			bench.save_settings(ready_settings(), path)
			with patch('gui.web_bindings.SETTINGS_PATH', path), \
				patch('gui.web_bindings.load_settings', wraps=bench.load_settings), \
				patch('gui.web_bindings.messagebox.showerror') as error:
				frame = BenchFrame(root)
				root.update_idletasks()
				self.assertEqual(frame.collect(), ready_settings())
				self.assertEqual(len(frame.feedback_tree.get_children()), 2)
				self.assertGreater(len(frame.canvas.find_all()), 10)
				frame.variables['web', 'password'].set('saved-test-password')
				self.assertTrue(frame.save())
				self.assertEqual(bench.load_settings(path)['web']['password'], 'saved-test-password')
				process = Mock()
				with patch('gui.web_bindings.subprocess.Popen', return_value=process) as popen, \
					patch('gui.web_bindings.threading.Thread'):
					frame.start(True)
					command = popen.call_args.args[0]
					self.assertIn('--check', command)
					self.assertNotIn('saved-test-password', ' '.join(command))
					snapshot = Path(command[command.index('--profile') + 1])
					self.assertEqual(bench.load_settings(snapshot)['web']['password'], 'saved-test-password')
					self.assertEqual(str(frame.editors[0][0]['state']), 'disabled')
					frame.stop()
					frame.stop()
					process.stdin.write.assert_called_once_with('stop\n')
					process.kill.assert_not_called()
					process.terminate.assert_not_called()
				frame.events.put(('exit', 130))
				frame.poll()
				self.assertIsNone(frame.process)
				self.assertFalse(snapshot.exists())
				self.assertEqual(str(frame.editors[0][0]['state']), 'normal')
				with patch('gui.web_bindings.messagebox.askyesno', return_value=False), \
					patch('gui.web_bindings.subprocess.Popen') as popen:
					frame.start(False)
					popen.assert_not_called()
				error.assert_not_called()


if __name__ == '__main__':
	unittest.main()
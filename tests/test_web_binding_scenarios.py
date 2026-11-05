import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import mainThread  # Preserve application import order without starting services.
import smartnet.constants as snc
from scenario.base.web_bindings import WebBindingScenario
from scenario.list.web.scenario_web_input_9_1_1 import Scenario as InputScenario
from scenario.list.web.scenario_web_relay_9_1_2 import Scenario as RelayScenario
from scenario.scenario import ThreadStoppedException
from smartnet.mapping_client import UNDEFINED_MAPPING, pack_mapping
from webapi.client import WebApiError


class WebBindingScenarioTests(unittest.TestCase):
	def test_dedicated_preset_has_no_virtual_io_or_initial_bindings(self):
		from presets.preset import get_presets_list, validate_program_presets
		programs, controllers = get_presets_list('web_bindings')
		validate_program_presets(programs)
		self.assertEqual(controllers, [])
		self.assertEqual(len(programs), 1)
		self.assertEqual(programs[0].get_id(), 101)
		self.assertEqual(programs[0].get_type(), snc.ProgramType.DOUBLE_PUMP)
		self.assertFalse(programs[0].is_virtual())
		self.assertEqual(programs[0].get_inputs(), [])
		self.assertEqual(programs[0].get_outputs(), [])

	def test_cli_http_options_are_optional_and_reject_unsafe_modes(self):
		from main import initArgParser
		self.assertIsNone(initArgParser('', []).web_url)
		args = initArgParser('', ['--web-url', 'http://localhost', '--id', '7'])
		self.assertEqual(args.web_login, 'admin')
		self.assertEqual(args.web_password_env, 'BRS_WEB_PASSWORD')
		for options in ([], ['--id', '0'], ['--id', '256'], ['--id', '7', '--debug'],
				['--id', '7', '--udp-ports', '31987'], ['--id', '7', '--can-worker']):
			with self.subTest(options=options), patch('sys.stderr'), self.assertRaises(SystemExit):
				initArgParser('', ['--web-url', 'http://localhost'] + options)

	def setUp(self):
		for name in ('print_log', 'print_error'):
			patcher = patch('scenario.base.web_bindings.' + name)
			patcher.start()
			self.addCleanup(patcher.stop)

	def make_scenario(self, scenario_type=InputScenario):
		scenario = scenario_type.__new__(scenario_type)
		scenario._controller_id = 7
		scenario._can = Mock()
		scenario._web = Mock()
		scenario._web.config.return_value = {'controllers': [{'id': 7, 'programs': [
			{'id': 101, 'type': int(snc.ProgramType.DOUBLE_PUMP)}]}]}
		scenario.is_stopped = Mock(return_value=False)
		scenario.wait = Mock()
		scenario.APPLY_TIMEOUT = 0  # Immediate mismatch, no wall-clock waits.
		state = {(kind, index): UNDEFINED_MAPPING for kind, count in (
			('input', 4), ('output', 5), ('relay', 11)) for index in range(count)}
		# Preserve non-default state on untouched channels and the tested input.
		state['input', 0] = pack_mapping(7, 3, 0)
		state['input', 1] = pack_mapping(7, 2, 0)
		state['relay', 10] = pack_mapping(200, 1, 5)
		for kind in ('input', 'output', 'relay'):
			getattr(scenario._can, f'read_{kind}').side_effect = lambda host, index, kind=kind: state[kind, index]
			getattr(scenario._can, f'restore_{kind}').side_effect = (
				lambda host, index, raw, kind=kind: state.__setitem__((kind, index), raw))
		def bind_input(program_id, input_id, controller_id, sensor_id):
			state['input', input_id] = pack_mapping(controller_id, sensor_id, 0)
			return {'partial': True, 'controllers': []}
		def unbind_input(program_id, input_id):
			state['input', input_id] = UNDEFINED_MAPPING
			return {'partial': True, 'controllers': []}
		def bind_relay(controller_id, relay_id, program_id, output_id):
			for index in (0, 1):
				state['output', index] = UNDEFINED_MAPPING
			state['relay', relay_id] = pack_mapping(program_id, output_id, 5)
			state['output', output_id] = pack_mapping(controller_id, relay_id, 1)
			return {'partial': True, 'controllers': []}
		def unbind_relay(controller_id, relay_id):
			state['relay', relay_id] = UNDEFINED_MAPPING
			for index in (0, 1):
				state['output', index] = UNDEFINED_MAPPING
			return {'partial': True, 'controllers': []}
		scenario._web.bind_input.side_effect = bind_input
		scenario._web.unbind_input.side_effect = unbind_input
		scenario._web.bind_relay.side_effect = bind_relay
		scenario._web.unbind_relay.side_effect = unbind_relay
		return scenario, state

	def test_both_sequences_and_restoration(self):
		for scenario_type in (InputScenario, RelayScenario):
			with self.subTest(scenario=scenario_type.__name__):
				scenario, state = self.make_scenario(scenario_type)
				before = dict(state)
				scenario.run()
				self.assertEqual(scenario._status, 'OK')
				self.assertEqual(state, before)
				scenario._web.login.assert_called_once()
				scenario._web.logout.assert_called_once()
				kind = 'input' if scenario_type is InputScenario else 'relay'
				self.assertEqual(getattr(scenario._web, f'bind_{kind}').call_count, 3)
				self.assertEqual(getattr(scenario._web, f'unbind_{kind}').call_count, 2)

	def test_http_timeout_after_application_restores_without_retry(self):
		for scenario_type, method in ((InputScenario, 'bind_input'), (RelayScenario, 'bind_relay')):
			with self.subTest(method=method):
				scenario, state = self.make_scenario(scenario_type)
				before = dict(state)
				operation = getattr(scenario._web, method)
				apply = operation.side_effect
				def fail(*args):
					apply(*args)
					raise WebApiError('unknown outcome')
				operation.side_effect = fail
				scenario.run()
				self.assertEqual(scenario._status, 'FAIL')
				self.assertEqual(state, before)
				operation.assert_called_once()

	def test_unexpected_changes_fail_and_are_restored(self):
		scenario, state = self.make_scenario()
		before = dict(state)
		apply = scenario._web.bind_input.side_effect
		def corrupt(*args):
			result = apply(*args)
			state['input', 1] = UNDEFINED_MAPPING
			return result
		scenario._web.bind_input.side_effect = corrupt
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(state, before)

	def test_reverse_output_mapping_is_checked(self):
		scenario, state = self.make_scenario(RelayScenario)
		before = dict(state)
		def missing_reverse(controller_id, relay_id, program_id, output_id):
			state['relay', relay_id] = pack_mapping(program_id, output_id, 5)
			return {'controllers': []}
		scenario._web.bind_relay.side_effect = missing_reverse
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(state, before)

	def test_cancellation_restores_and_propagates(self):
		scenario, state = self.make_scenario()
		before = dict(state)
		scenario.is_stopped.side_effect = [False, True]
		with self.assertRaises(ThreadStoppedException):
			scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(state, before)
		scenario._web.logout.assert_called_once()

	def test_restoration_failure_never_reports_ok_and_continues_other_endpoints(self):
		scenario, state = self.make_scenario(RelayScenario)
		scenario._can.restore_output.side_effect = RuntimeError('CAN offline')
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(scenario._can.restore_output.call_count, 2)
		scenario._can.restore_relay.assert_called_once()
		scenario._web.logout.assert_called_once()

	def test_unsafe_initial_state_or_wrong_http_target_never_mutates(self):
		for problem in ('output', 'relay', 'input', 'http_id', 'http_program', 'login', 'can'):
			with self.subTest(problem=problem):
				scenario, state = self.make_scenario()
				if problem == 'output':
					state['output', 0] = pack_mapping(7, 1, 1)
				elif problem == 'relay':
					state['relay', 0] = pack_mapping(200, 1, 5)
				elif problem == 'input':
					state['input', 0] = pack_mapping(200, 1, 5)
				elif problem == 'http_id':
					scenario._web.config.return_value = {'controllers': []}
				elif problem == 'http_program':
					scenario._web.config.return_value['controllers'][0]['programs'] = []
				elif problem == 'login':
					scenario._web.login.side_effect = WebApiError('access denied')
				else:
					scenario._can.read_input.side_effect = RuntimeError('CAN timeout')
				before = dict(state)
				scenario.run()
				self.assertEqual(scenario._status, 'FAIL')
				self.assertEqual(state, before)
				for method in ('bind_input', 'unbind_input', 'bind_relay', 'unbind_relay'):
					getattr(scenario._web, method).assert_not_called()

	def test_logout_failure_marks_test_failed(self):
		scenario, state = self.make_scenario()
		before = dict(state)
		scenario._web.logout.side_effect = WebApiError('offline')
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(state, before)

	def test_missing_http_configuration_is_rejected_before_preset_loading(self):
		scenario = WebBindingScenario.__new__(WebBindingScenario)
		with patch('scenario.base.web_bindings.mainThread.MainThread', return_value=SimpleNamespace(web_client=None)), \
				patch('scenario.base.web_bindings.main.loadPreset') as load_preset:
			with self.assertRaisesRegex(RuntimeError, '--web-url'):
				scenario.init_scenario()
			load_preset.assert_not_called()

	def make_initializing_scenario(self):
		scenario = WebBindingScenario.__new__(WebBindingScenario)
		scenario._controllerHost = Mock()
		scenario._controllerHost.get_controller_id.return_value = 7
		scenario._controllerHost.get_virtual_outdoor_preset.return_value = None
		scenario._virtual_outdoor = None
		scenario.wait = Mock()
		program = Mock()
		program.get_id.return_value = 101
		program.get_type.return_value = snc.ProgramType.DOUBLE_PUMP
		scenario._controllerHost.get_program_list.return_value = []
		def load_preset(preset, **options):
			self.assertEqual(preset, 'web_bindings')
			self.assertTrue(options['scenario'])
			scenario._controllerHost.get_program_list.return_value = [program]
		services = SimpleNamespace(worker=Mock(web_client=Mock(), _debug=False), program=program)
		for name, target, options in (
			('worker_accessor', 'mainThread.MainThread', {'return_value': services.worker}),
			('load_preset', 'main.loadPreset', {'side_effect': load_preset}),
			('load_done', 'main.loadPresetDone', {'return_value': True}),
			('load_succeeded', 'main.load_preset_succeeded', {'return_value': True}),
			('load_error', 'main.get_preset_error', {'return_value': 'test load rejected'}),
			('can_factory', 'scenario.base.web_bindings.MappingCanClient', {}),
		):
			patcher = patch(target, **options)
			setattr(services, name, patcher.start())
			self.addCleanup(patcher.stop)
		services.can_factory.return_value.read_channel_counts.return_value = (18, 11)
		return scenario, services

	def test_preparation_automatically_loads_preset_without_selected_profile(self):
		scenario, services = self.make_initializing_scenario()
		services.worker.getCurrentPreset.return_value = 'other'
		scenario.init_scenario()
		services.load_preset.assert_called_once_with('web_bindings', scenario=True)
		services.can_factory.return_value.read_channel_counts.assert_called_once_with(7)
		self.assertIs(scenario._programList['test_program'], services.program)
		services.program.disable_gui_control.assert_called_once()
		services.worker.getCurrentPreset.assert_not_called()

	def test_every_run_reloads_even_if_test_program_is_already_present(self):
		scenario, services = self.make_initializing_scenario()
		scenario._controllerHost.get_program_list.return_value = [services.program]
		for _ in range(2):
			scenario.init_scenario()
		self.assertEqual(services.load_preset.call_count, 2)
		self.assertEqual(services.load_succeeded.call_count, 2)

	def test_wrong_channel_counts_are_rejected_before_reset(self):
		scenario, services = self.make_initializing_scenario()
		services.can_factory.return_value.read_channel_counts.return_value = (6, 8)
		with self.assertRaisesRegex(RuntimeError, 'Expected xhcc_s62'):
			scenario.init_scenario()
		services.load_preset.assert_not_called()
		services.program.disable_gui_control.assert_not_called()

	def test_waits_for_startup_and_scenario_preset_loading(self):
		scenario, services = self.make_initializing_scenario()
		services.load_done.side_effect = [False, True, False, True]
		scenario.init_scenario()
		self.assertEqual(services.load_done.call_count, 4)
		self.assertEqual(scenario.wait.call_count, 3)  # Startup, reload, shared settle wait.
		services.load_succeeded.assert_called_once()

	def test_failed_preset_load_aborts_initialization(self):
		scenario, services = self.make_initializing_scenario()
		services.load_succeeded.return_value = False
		with self.assertRaisesRegex(RuntimeError, 'test load rejected'):
			scenario.init_scenario()
		services.program.disable_gui_control.assert_not_called()
		services.worker.web_client.bind_input.assert_not_called()

	def test_missing_program_after_loading_is_rejected(self):
		scenario, services = self.make_initializing_scenario()
		services.load_preset.side_effect = None
		with self.assertRaisesRegex(RuntimeError, 'missing required programs'):
			scenario.init_scenario()
		services.program.disable_gui_control.assert_not_called()

	def test_unexpected_program_id_after_loading_is_rejected(self):
		scenario, services = self.make_initializing_scenario()
		services.program.get_id.return_value = 102
		with self.assertRaisesRegex(RuntimeError, 'Unexpected web test program ID'):
			scenario.init_scenario()
		services.worker.web_client.bind_input.assert_not_called()

	def test_preset_wait_is_cancellable(self):
		scenario, services = self.make_initializing_scenario()
		services.load_done.side_effect = [True, False]
		scenario.wait.side_effect = ThreadStoppedException('cancelled')
		with self.assertRaises(ThreadStoppedException):
			scenario.init_scenario()
		services.load_preset.assert_called_once_with('web_bindings', scenario=True)
		services.program.disable_gui_control.assert_not_called()
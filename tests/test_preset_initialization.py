"""Preset setup must not be mistaken for successful scenario preparation."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import threading
import unittest
from unittest.mock import Mock, patch

from presets.preset import ProgramPreset
from scenario import scenario as scenarios
import smartnet.constants as snc


class PresetInitializationTests(unittest.TestCase):
	def setUp(self):
		self.worker = SimpleNamespace(_guiThread=None, _preset_error=None, setCurrentPreset=Mock())

	def test_binding_or_setting_failure_rejects_preset(self):
		for stage in ('input', 'output', 'parameter'):
			with self.subTest(stage=stage):
				parameter = Mock()
				parameter.write.return_value = stage != 'parameter'
				program = ProgramPreset(snc.ProgramType.SNOWMELT, 'DEFAULT', 101, 'snow',
					SimpleNamespace(get=lambda: [parameter]), [object()], [object()])
				controller = Mock()
				controller.sendProgramAddRequest.return_value = True
				instance = controller.addProgramFromPreset.return_value
				instance.bind_input.return_value = stage != 'input'
				instance.bind_output.return_value = stage != 'output'
				with self.assertRaisesRegex(RuntimeError, stage):
					program.loadPreset(controller)

	def test_unconfirmed_controller_reset_rejects_preset(self):
		from controllers.controller import Controller
		controller = object.__new__(Controller)
		controller._programList = []
		controller._activeProgramsList = []
		controller._gui = None
		controller.resetConfig = Mock(return_value=False)
		with self.assertRaisesRegex(RuntimeError, 'reset'):
			controller.initController(True, [])

	def test_failed_preset_load_retains_cause(self):
		path = Path(__file__).resolve().parents[1] / 'mainThread.py'
		spec = importlib.util.spec_from_file_location('preset_test_main_thread', path)
		runtime = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(runtime)
		with (patch.object(runtime, 'MainThread', return_value=self.worker),
				patch.object(runtime.presets.preset, 'get_presets_list', return_value=([], [])),
				patch.object(runtime.cc, 'Controller') as controller,
				patch.object(runtime.ss, 'Simulator') as simulator):
			controller.return_value.initController.return_value = False
			self.assertFalse(runtime.loadPresetNow('invalid'))
		self.assertIn('invalid', str(self.worker._preset_error))
		self.worker.setCurrentPreset.assert_not_called()
		simulator.return_value.clear.assert_called()
		controller.return_value.clear.assert_called()

	def test_failed_simulator_reload_rejects_partially_loaded_preset(self):
		path = Path(__file__).resolve().parents[1] / 'mainThread.py'
		spec = importlib.util.spec_from_file_location('reload_test_main_thread', path)
		runtime = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(runtime)
		with (patch.object(runtime, 'MainThread', return_value=self.worker),
				patch.object(runtime.presets.preset, 'get_presets_list', return_value=([], [])),
				patch.object(runtime.cc, 'Controller') as controller,
				patch.object(runtime.ccio, 'initVirtualControllers'),
				patch.object(runtime.ss, 'Simulator') as simulator):
			controller.return_value.initController.return_value = True
			simulator.return_value.reloadConfig.side_effect = ValueError('bad channel')
			self.assertFalse(runtime.loadPresetNow('invalid'))
		self.assertIn('bad channel', str(self.worker._preset_error))
		self.worker.setCurrentPreset.assert_not_called()
		simulator.return_value.clear.assert_called()
		controller.return_value.clear.assert_called()

	def test_simulator_clear_unsubscribes_virtual_controllers(self):
		from simulator.simulator import Simulator
		virtual_controller = Mock()
		simulator = SimpleNamespace(_state_lock=threading.RLock(), _simList=[],
			_controllerIo=[virtual_controller], _clear_state=Mock())
		Simulator.clear(simulator)
		virtual_controller.clear.assert_called_once()
		simulator._clear_state.assert_called_once()

	def make_scenario(self):
		obj = object.__new__(scenarios.Scenario)
		obj._controllerHost = Mock()
		obj._EventStop = threading.Event()
		obj._manualSensorsList = []
		obj.get_default_preset = lambda: 'invalid'
		obj.get_required_programs = lambda: {'snow': 1}
		obj.force_preset_load = lambda: True
		obj.wait = Mock(return_value=True)
		obj.init_program_list = Mock(return_value=False)
		return obj

	def test_failed_load_stops_before_program_setup(self):
		obj = self.make_scenario()
		with (patch.object(scenarios.main, 'loadPreset'),
				patch.object(scenarios.main, 'loadPresetDone', return_value=True),
				patch.object(scenarios.main, 'load_preset_succeeded', return_value=False),
				patch.object(scenarios.main, 'get_preset_error', return_value=ValueError('bad input'))):
			with self.assertRaisesRegex(RuntimeError, 'bad input'):
				obj.init_scenario()
		obj.init_program_list.assert_not_called()
		obj._controllerHost.get_program_list.assert_not_called()

	def test_missing_programs_stops_after_successful_load(self):
		obj = self.make_scenario()
		with (patch.object(scenarios.main, 'loadPreset'),
				patch.object(scenarios.main, 'loadPresetDone', return_value=True),
				patch.object(scenarios.main, 'load_preset_succeeded', return_value=True)):
			with self.assertRaisesRegex(RuntimeError, 'missing required programs'):
				obj.init_scenario()

	def test_success_initializes_before_running(self):
		obj = self.make_scenario()
		obj.init_program_list.return_value = True
		obj._controllerHost.get_program_list.return_value = [Mock()]
		with (patch.object(scenarios.main, 'loadPreset'),
				patch.object(scenarios.main, 'loadPresetDone', return_value=True),
				patch.object(scenarios.main, 'load_preset_succeeded', return_value=True)):
			obj.init_scenario()
		obj._controllerHost.get_program_list.return_value[0].disable_gui_control.assert_called_once()

	def test_construction_error_reported_with_checklist_id(self):
		thread = object.__new__(scenarios.ScenarioThread)
		thread._controllerHost = Mock()
		thread._simulator = Mock()
		thread._progress_callback = None
		thread._result_callback = Mock()
		class InvalidScenario:
			def __init__(self, *args):
				raise RuntimeError('preset failed')
			def get_checklist_id(self):
				return '5.2.2.4'
		with patch.object(scenarios, 'importfile', return_value=SimpleNamespace(Scenario=InvalidScenario)):
			with self.assertRaisesRegex(RuntimeError, 'preset failed') as failure:
				thread.get_scenario_object('test.py')
		thread._report_failure('test.py', failure.exception)
		result = thread._result_callback.call_args.args[0]
		self.assertEqual(result['checklistId'], '5.2.2.4')
		self.assertEqual(result['result'], 'ERROR')


if __name__ == '__main__':
	unittest.main()
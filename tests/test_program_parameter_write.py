"""Program parameter-write contracts without application startup or CAN I/O."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch
import warnings

import smartnet.constants as snc


def load_program_module():
	smartnet = ModuleType('smartnet')
	smartnet.constants = snc
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	message = ModuleType('smartnet.message')
	channels = ModuleType('smartnet.channelMapping')
	channels.InputChannel = Mock()
	channels.OutputChannel = Mock()
	smartnet.remoteControl = remote
	smartnet.message = message
	smartnet.channelMapping = channels
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	path = Path(__file__).resolve().parents[1] / 'programs/program.py'
	spec = importlib.util.spec_from_file_location('program_parameter_write_test', path)
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {
		'smartnet': smartnet, 'smartnet.constants': snc,
		'smartnet.remoteControl': remote, 'smartnet.message': message,
		'smartnet.channelMapping': channels, 'consoleLog': console,
	}):
		spec.loader.exec_module(module)
	return module


program_module = load_program_module()


class TestProgramParameterWrite(unittest.TestCase):
	def setUp(self):
		self.program = Mock()
		self.program.get_parameter_code.return_value = (1, 2)
		self.program.get_id.return_value = 101
		factory_patch = patch.object(program_module.sr, 'RemoteControlParameter')
		self.factory = factory_patch.start()
		self.addCleanup(factory_patch.stop)

	def test_write_returns_status_independently_of_value(self):
		for value in (0, 25):
			for status in (True, False):
				with self.subTest(value=value, status=status):
					self.factory.return_value.write.return_value = status
					result = program_module.Program.write_parameter(self.program, 'setting', value)
					self.assertIs(result, status)
					self.factory.return_value.write.assert_called_with(True)
					self.factory.return_value.get_value.assert_not_called()

	def test_write_passes_index_and_confirmation(self):
		self.factory.return_value.write.return_value = True
		result = program_module.Program.write_parameter(
			self.program, 'setting', 0, index=3, confirm=False)
		self.assertIs(result, True)
		self.program.get_parameter_code.assert_called_once_with('setting')
		self.factory.assert_called_once_with(
			parameterCode=(1, 2), programId=101, parameterValue=0, parameterIndex=3)
		self.factory.return_value.write.assert_called_once_with(False)

	def test_unknown_parameter_returns_false_without_writing(self):
		self.program.get_parameter_code.return_value = None
		self.assertIs(program_module.Program.write_parameter(self.program, 'unknown', 5), False)
		self.factory.assert_not_called()

	def test_legacy_method_warns_and_preserves_value_even_on_failure(self):
		for value in (0, 25):
			with self.subTest(value=value):
				self.factory.return_value.write.return_value = False
				self.factory.return_value.get_value.return_value = value
				with warnings.catch_warnings(record=True) as caught:
					warnings.simplefilter('always', DeprecationWarning)
					result = program_module.Program.write_parameter_value(
						self.program, 'setting', value, index=3, confirm=False)
				self.assertEqual(result, value)
				self.assertEqual(len(caught), 1)
				self.assertIs(caught[0].category, DeprecationWarning)
				self.assertIn('use write_parameter()', str(caught[0].message))
				self.assertEqual(Path(caught[0].filename).resolve(), Path(__file__).resolve())
				self.factory.assert_called_with(
					parameterCode=(1, 2), programId=101, parameterValue=value, parameterIndex=3)
				self.factory.return_value.write.assert_called_with(False)

	def test_legacy_unknown_parameter_still_returns_none(self):
		self.program.get_parameter_code.return_value = None
		with self.assertWarns(DeprecationWarning):
			result = program_module.Program.write_parameter_value(self.program, 'unknown', 5)
		self.assertIsNone(result)
		self.factory.assert_not_called()


if __name__ == '__main__':
	unittest.main()
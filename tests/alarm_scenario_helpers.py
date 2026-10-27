"""Shared hardware-free fixtures for filling-loop alarm scenarios."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]


def load_alarm_scenario(relative_path):
	def load(name, path):
		spec = importlib.util.spec_from_file_location(name, ROOT / path)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return module

	parent = ModuleType('scenario.scenario')
	parent.Scenario = object
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	with patch.dict(sys.modules, {
		'scenario.scenario': parent,
		'smartnet.remoteControl': remote,
		'consoleLog': console,
	}):
		base = load('filling_alarm_base_under_test', 'scenario/base/filling_loop_alarm.py')
		with patch.dict(sys.modules, {'scenario.base.filling_loop_alarm': base}):
			return load('filling_alarm_scenario_under_test', relative_path).Scenario


class Sensor:
	def __init__(self, value):
		self.value = value
		self.manual = False
		self.mapped = True

	def get_value(self):
		return self.value

	def set_value(self, value, manual=False):
		self.value = value

	def is_mapped(self):
		return self.mapped

	def isManual(self):
		return self.manual

	def set_manual(self, manual):
		self.manual = manual

	def isShort(self):
		return False

	def isOpen(self):
		return False
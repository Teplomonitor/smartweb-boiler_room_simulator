"""Summer scenario orchestration with stubbed controller replies, not firmware integration."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc


def load_scenario():
	parent = ModuleType('scenario.scenario')
	parent.Scenario = type('Parent', (), {'RELAY_ON': 255, 'RELAY_OFF': 0})
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	path = Path(__file__).resolve().parents[1] / 'scenario/list/heating_circuit/scenario_heating_circuit_3_3_4.py'
	spec = importlib.util.spec_from_file_location('summer_scenario_under_test', path)
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {
		'scenario.scenario': parent, 'smartnet.remoteControl': remote, 'consoleLog': console,
	}):
		spec.loader.exec_module(module)
	return module


module = load_scenario()


class TestHeatingCircuitSummerScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = module.Scenario()
		self.temperature = -10
		self.manual = False
		self.sensor = Mock()
		self.sensor.get_value.side_effect = lambda: self.temperature
		self.sensor.isManual.side_effect = lambda: self.manual
		self.sensor.isShort.return_value = False
		self.sensor.isOpen.return_value = False
		self.sensor.set_value.side_effect = self.set_temperature
		self.sensor.set_manual.side_effect = self.set_manual
		self.pump = Mock()
		self.circuit = Mock()
		self.circuit.get_output_channel.return_value = self.pump
		outdoor = Mock()
		outdoor.get_input_channel.return_value = self.sensor
		self.scenario._programList = {'heating_circuit': self.circuit, 'outdoor': outdoor, 'boiler': Mock()}
		self.initial_values = {
			(program_type, parameter_id): value
			for (program_type, parameter_id, _), value in zip(self.scenario._settings(), (2, 22, 0, 45))
		}
		self.values = self.initial_values.copy()
		self.scenario._read_parameter = Mock(side_effect=self.read_parameter)
		self.scenario._write_parameter = Mock(side_effect=self.write_parameter)
		self.scenario.wait_event = Mock(side_effect=lambda predicate, timeout: predicate())
		self.scenario.wait_state_permanence = Mock(side_effect=self.observe_state)
		self.phases = []
		self.fault = None

	def set_temperature(self, value, manual):
		self.temperature = value

	def set_manual(self, value):
		self.manual = value

	def read_parameter(self, program_type, parameter_id):
		if (program_type, parameter_id) == (snc.ProgramType.CIRCUIT, snc.CircuitParameterId.OUTDOOR_TEMPERATURE):
			return None if self.fault == 'outdoor' else self.temperature
		if (program_type, parameter_id) == (snc.ProgramType.CONSUMER, snc.ConsumerParameterId.REQUIRED_TEMPERATURE):
			if self.fault == 'request':
				return None
			if self.fault == 'still_heating':
				return 40
			return 40 if self.temperature == 15 else 'OPEN'
		return self.values[program_type, parameter_id]

	def write_parameter(self, program_type, parameter_id, value):
		self.values[program_type, parameter_id] = value
		return True

	def observe_state(self, predicate, duration, timeout):
		# Reference replies exercise predicates only, without simulating firmware regulation.
		self.phases.append(self.temperature)
		state = 255 if self.temperature == 15 else 0
		if self.fault == 'stuck_on':
			state = 255
		elif self.fault == 'stuck_off' or (self.fault == 'no_recovery' and len(self.phases) == 3):
			state = 0
		self.pump.get_value.return_value = state
		return all(predicate() for _ in range(3))

	def assert_restored(self, manual=False):
		self.assertEqual(self.temperature, -10)
		self.assertEqual(self.manual, manual)
		self.assertEqual(self.values, self.initial_values)

	def test_success_and_timeouts(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.phases, [15, 25, 15])
		self.assertEqual(
			[call.args[2] for call in self.scenario.wait_state_permanence.call_args_list],
			[120, 180, 120],
		)
		self.assert_restored()

	def test_faults_fail_and_restore(self):
		for fault in ('outdoor', 'request', 'still_heating', 'stuck_on', 'stuck_off', 'no_recovery'):
			with self.subTest(fault=fault):
				self.phases.clear()
				self.fault = fault
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assert_restored()

	def test_preexisting_manual_mode_is_preserved(self):
		self.manual = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assert_restored(manual=True)

	def test_missing_mappings_prevent_writes(self):
		for channel in (self.sensor, self.pump):
			channel.is_mapped.return_value = False
			self.scenario.run()
			self.assertEqual(self.scenario._status, 'FAIL')
			self.scenario._write_parameter.assert_not_called()
			channel.is_mapped.return_value = True

	def test_invalid_initial_sensor_prevents_writes(self):
		for value in (None, 'OPEN', float('nan')):
			self.temperature = value
			self.scenario.run()
			self.assertEqual(self.scenario._status, 'FAIL')
			self.scenario._write_parameter.assert_not_called()

	def test_failed_read_prevents_writes(self):
		self.scenario._read_parameter.side_effect = None
		self.scenario._read_parameter.return_value = None
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.scenario._write_parameter.assert_not_called()
		self.assert_restored()

	def test_failed_write_restores_partial_settings(self):
		def write(*args):
			if self.scenario._write_parameter.call_count == 2:
				return None
			return self.write_parameter(*args)
		self.scenario._write_parameter.side_effect = write
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_stop_exception_restores_all(self):
		self.scenario.wait_state_permanence.side_effect = RuntimeError('stopped')
		with self.assertRaisesRegex(RuntimeError, 'stopped'):
			self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assert_restored()

	def test_restore_failure_does_not_skip_sensor_or_other_parameters(self):
		def write(*args):
			if self.scenario._write_parameter.call_count == 5:
				raise RuntimeError('restore failed')
			return self.write_parameter(*args)
		self.scenario._write_parameter.side_effect = write
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.scenario._write_parameter.call_count, 8)
		self.assertEqual(self.temperature, -10)
		self.assertFalse(self.manual)
		for key in list(self.initial_values)[:-1]:
			self.assertEqual(self.values[key], self.initial_values[key])


if __name__ == '__main__':
	unittest.main()
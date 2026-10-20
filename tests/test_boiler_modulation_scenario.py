"""Scenario 3.5.7 control flow with fake parameter I/O (not an integration test)."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import smartnet.constants as snc


def load_scenario():
	parent = ModuleType('scenario.scenario')
	parent.Scenario = object
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	smartnet = ModuleType('smartnet')
	smartnet.constants = snc
	smartnet.remoteControl = remote
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	path = Path(__file__).resolve().parents[1] / 'scenario/list/boiler/scenario_boiler_3_5_7.py'
	spec = importlib.util.spec_from_file_location('boiler_modulation_scenario_test', path)
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {
		'scenario.scenario': parent, 'smartnet': smartnet,
		'smartnet.constants': snc, 'smartnet.remoteControl': remote, 'consoleLog': console,
	}):
		spec.loader.exec_module(module)
	return module.Scenario


Scenario = load_scenario()


class TestBoilerModulationScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = Scenario()
		self.boiler = Mock()
		self.circuit = Mock()
		self.scenario._programList = {'boiler': self.boiler, 'heating_circuit': self.circuit}
		for program in (self.boiler, self.circuit):
			program.get_input_channel.return_value.is_mapped.return_value = True
			program.get_input_channel.return_value.isManual.return_value = False
		self.boiler.get_stage_1.return_value.is_mapped.return_value = False
		self.boiler.get_output_channel.return_value.is_mapped.return_value = False
		self.boiler.get_power_output.return_value.is_mapped.return_value = True
		self.values = {'heatCalculationMode': 0, 'temperatureCompensation': 5, 'requiredConstantFlowTemperature': 35}
		self.initial_values = self.values.copy()
		self.circuit.read_parameter_value.side_effect = self.values.get
		# The legacy API returns a value (including zero), NOT write success.
		self.circuit.write_parameter_value.side_effect = lambda name, value: value
		self.circuit.get_id.return_value = 101
		self.parameter_codes = {
			'heatCalculationMode': (snc.ProgramType.CIRCUIT, snc.CircuitParameterId.HEAT_CALCULATION_MODE),
			'temperatureCompensation': (snc.ProgramType.CONSUMER, snc.ConsumerParameterId.TEMPERATURE_COMPENSATION),
			'requiredConstantFlowTemperature': (snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE),
		}
		self.circuit.get_parameter_code.side_effect = self.parameter_codes.__getitem__
		self.writes = Mock(side_effect=self.write_parameter)
		remote = Scenario._write_circuit_parameter.__globals__['sr']
		factory_patch = patch.object(remote, 'RemoteControlParameter', side_effect=self.make_parameter)
		self.parameter_factory = factory_patch.start()
		self.addCleanup(factory_patch.stop)
		self.boiler.get_temperature.side_effect = lambda: self.values['requiredConstantFlowTemperature']
		self.sample_index = 0
		self.boiler.get_power_output_percent.side_effect = self.power
		self.scenario._read_required_temperature = Mock(side_effect=lambda: self.values['requiredConstantFlowTemperature'])
		self.scenario.wait_event = Mock(side_effect=lambda predicate, timeout: predicate())
		self.scenario.wait_value_maintaining = Mock(side_effect=self.check_maintaining)

	def power(self):
		self.sample_index += 1
		return (20, 50, 80)[self.sample_index % 3]

	def write_parameter(self, name, value):
		self.values[name] = value
		return True

	def make_parameter(self, *, parameterCode, programId, parameterValue):
		self.assertEqual(programId, 101)
		name = next(name for name, code in self.parameter_codes.items() if code == parameterCode)
		parameter = Mock()
		parameter.get_value.return_value = parameterValue
		parameter.write.side_effect = lambda: self.writes(name, parameterValue)
		return parameter

	def check_maintaining(self, value_handler, required_handler, **kwargs):
		for _ in range(3):
			self.assertEqual(value_handler(), required_handler())
		self.assertEqual(kwargs['dtAvrMax'], Scenario.AVERAGE_ERROR_LIMIT)
		self.assertNotIn('supplyValueHandler', kwargs)
		return True

	def assert_failed_and_restored(self):
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.values, self.initial_values)

	def test_success_uses_shared_helper_and_restores_parameters(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.values, self.initial_values)
		self.assertEqual(self.scenario.wait_value_maintaining.call_count, 3)
		writes = [call.args[1] for call in self.writes.call_args_list if call.args[0] == 'requiredConstantFlowTemperature']
		self.assertEqual(writes, [45, 45, 60, 45, 35])
		self.circuit.write_parameter_value.assert_not_called()
		for program in (self.boiler, self.circuit):
			program.get_input_channel.return_value.set_manual.assert_not_called()
			program.get_input_channel.return_value.set_value.assert_not_called()

	def test_zero_compensation_is_written_and_restored_successfully(self):
		self.values['temperatureCompensation'] = 0
		self.initial_values = self.values.copy()
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.values, self.initial_values)
		compensation_writes = [call.args[1] for call in self.writes.call_args_list if call.args[0] == 'temperatureCompensation']
		self.assertEqual(compensation_writes, [0, 0])
		self.parameter_factory.assert_any_call(
			parameterCode=self.parameter_codes['temperatureCompensation'],
			programId=101, parameterValue=0,
		)

	def test_nonzero_setpoint_write_failure_is_not_accepted_as_success(self):
		def write(name, value):
			if name == 'requiredConstantFlowTemperature' and value == 60:
				return False
			return self.write_parameter(name, value)
		self.writes.side_effect = write
		self.scenario.run()
		self.assert_failed_and_restored()
		self.assertEqual(self.scenario.wait_value_maintaining.call_count, 1)

	def test_frozen_power_or_only_discrete_switching_is_rejected(self):
		for power in (lambda: 50, lambda: 100 if self.power() > 50 else 0):
			with self.subTest(power=power):
				self.boiler.get_power_output_percent.side_effect = power
				self.scenario.run()
				self.assert_failed_and_restored()

	def test_missing_or_invalid_measurements_fail_cleanly(self):
		for value in (None, float('nan'), float('inf')):
			with self.subTest(value=value):
				self.boiler.get_temperature.side_effect = None
				self.boiler.get_temperature.return_value = value
				self.scenario.run()
				self.assert_failed_and_restored()

	def test_missing_power_fails_cleanly(self):
		self.boiler.get_power_output_percent.side_effect = None
		self.boiler.get_power_output_percent.return_value = None
		self.scenario.run()
		self.assert_failed_and_restored()

	def test_request_timeout_settling_timeout_and_control_failure(self):
		for responses in ((False,), (True, False)):
			with self.subTest(responses=responses):
				self.scenario.wait_event.side_effect = responses
				self.scenario.run()
				self.assert_failed_and_restored()
		self.scenario.wait_event.side_effect = lambda predicate, timeout: predicate()
		self.scenario.wait_value_maintaining.side_effect = None
		self.scenario.wait_value_maintaining.return_value = False
		self.scenario.run()
		self.assert_failed_and_restored()

	def test_lost_setpoint_during_control_is_not_silently_accepted(self):
		def lose_setpoint(*args, **kwargs):
			self.scenario._read_required_temperature.return_value = None
			self.scenario._read_required_temperature.side_effect = None
			return self.check_maintaining(*args, **kwargs)
		self.scenario.wait_value_maintaining.side_effect = lose_setpoint
		self.scenario.run()
		self.assert_failed_and_restored()

	def test_missing_parameter_or_manual_sensor_prevents_writes(self):
		self.circuit.read_parameter_value.side_effect = None
		self.circuit.read_parameter_value.return_value = None
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.writes.assert_not_called()
		self.boiler.get_input_channel.return_value.isManual.return_value = True
		self.scenario.run()
		self.writes.assert_not_called()

	def test_wrong_boiler_mapping_is_rejected(self):
		self.boiler.get_stage_1.return_value.is_mapped.return_value = True
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.writes.assert_not_called()

	def test_partial_setup_failure_restores_all_settings(self):
		def write(name, value):
			if name == 'temperatureCompensation' and value == 0:
				return None
			return self.write_parameter(name, value)
		self.writes.side_effect = write
		self.scenario.run()
		self.assert_failed_and_restored()

	def test_exception_or_external_stop_restores_parameters(self):
		self.scenario.wait_value_maintaining.side_effect = RuntimeError('stopped')
		with self.assertRaises(RuntimeError):
			self.scenario.run()
		self.assert_failed_and_restored()

	def test_restoration_continues_after_error(self):
		for raises in (False, True):
			with self.subTest(raises=raises):
				self.values = self.initial_values.copy()
				def write(name, value):
					if name == 'requiredConstantFlowTemperature' and value == 35:
						if raises:
							raise RuntimeError('restore failure')
						return False
					return self.write_parameter(name, value)
				self.writes.side_effect = write
				self.circuit.read_parameter_value.side_effect = self.values.get
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				for name in ('heatCalculationMode', 'temperatureCompensation'):
					self.assertEqual(self.values[name], self.initial_values[name])


if __name__ == '__main__':
	unittest.main()
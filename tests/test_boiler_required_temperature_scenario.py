"""Exercise the scenario with fake parameter I/O, without GUI or CAN imports."""

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
	smartnet = ModuleType('smartnet')
	smartnet.constants = snc
	smartnet.remoteControl = remote
	console = ModuleType('consoleLog')
	console.print_log = Mock()
	console.print_error = Mock()
	path = Path(__file__).resolve().parents[1] / 'scenario/list/boiler/scenario_boiler_3_5_4.py'
	spec = importlib.util.spec_from_file_location('boiler_scenario_under_test', path)
	module = importlib.util.module_from_spec(spec)
	with patch.dict(sys.modules, {
		'scenario.scenario': parent,
		'smartnet': smartnet,
		'smartnet.constants': snc,
		'smartnet.remoteControl': remote,
		'consoleLog': console,
	}):
		spec.loader.exec_module(module)
	return module.Scenario


Scenario = load_scenario()


class TestBoilerRequiredTemperatureScenario(unittest.TestCase):
	def setUp(self):
		self.scenario = Scenario()
		self.circuits = [Mock() for _ in range(4)]
		for index, circuit in enumerate(self.circuits, 101):
			circuit.get_id.return_value = index
		boiler = Mock()
		boiler.get_id.return_value = 105
		boiler.get_minimum_temperature.return_value = 20
		boiler.get_maximum_temperature.return_value = 80
		boiler.get_minimum_temperature_restriction.return_value = 0
		self.scenario._boiler = boiler
		self.scenario._programList = {'boiler': boiler}
		self.scenario._programList.update({
			f'heating_circuit_{index}': circuit
			for index, circuit in enumerate(self.circuits, 1)
		})
		self.values = {}
		for circuit in self.circuits:
			for parameter, value in zip(Scenario.CIRCUIT_PARAMETERS, (0, 35, 15, 85)):
				self.values[snc.ProgramType.CIRCUIT, parameter, circuit.get_id()] = value
			self.values[snc.ProgramType.CONSUMER, snc.ConsumerParameterId.TEMPERATURE_COMPENSATION, circuit.get_id()] = 5
		self.restriction_key = (
			snc.ProgramType.TEMPERATURE_GENERATOR,
			snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
			105,
		)
		self.values[self.restriction_key] = 0
		self.initial_values = self.values.copy()
		self.fault = None
		self.high_water_mark = 0
		self.scenario._read_parameter = Mock(side_effect=self.read_parameter)
		self.scenario._write_parameter = Mock(side_effect=self.write_parameter)
		self.scenario.wait_event = Mock(side_effect=lambda predicate, timeout: predicate())
		self.scenario.wait_state_permanence = Mock(
			side_effect=lambda predicate, duration: all(predicate() for _ in range(3)),
		)

	def flow(self, program_id):
		return self.values[
			snc.ProgramType.CIRCUIT,
			snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE,
			program_id,
		]

	def shift(self, program_id):
		return self.values[
			snc.ProgramType.CONSUMER,
			snc.ConsumerParameterId.TEMPERATURE_COMPENSATION,
			program_id,
		]

	def read_parameter(self, program_type, parameter_id, program_id):
		if (program_type, parameter_id) == (
			snc.ProgramType.CONSUMER, snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
		):
			return self.flow(program_id)
		if (program_type, parameter_id) == (
			snc.ProgramType.TEMPERATURE_SOURCE,
			snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE,
		):
			requests = []
			for circuit in self.circuits:
				identifier = circuit.get_id()
				if self.fault == 'ignore_fourth' and identifier == 104:
					continue
				shift = self.shift(identifier)
				if self.fault == 'ignore_shift':
					shift = 0
				elif self.fault == 'double_shift':
					shift *= 2
				requests.append(max(0, min(100, self.flow(identifier) + shift)))
			if self.fault == 'frozen':
				return 20
			if self.fault == 'no_upper_limit':
				return max(20, max(requests))
			if self.fault == 'no_lower_limit':
				return min(80, max(requests))
			if self.fault == 'choose_before_shift':
				winner = max(self.circuits, key=lambda circuit: self.flow(circuit.get_id()))
				identifier = winner.get_id()
				return max(20, min(80, self.flow(identifier) + self.shift(identifier)))
			if self.fault == 'remember_maximum':
				self.high_water_mark = max(self.high_water_mark, max(requests))
				return max(20, min(80, self.high_water_mark))
			return max(20, min(80, max(requests)))
		return self.values[program_type, parameter_id, program_id]

	def write_parameter(self, program_type, parameter_id, program_id, value):
		self.values[program_type, parameter_id, program_id] = value
		return True

	def test_success_restores_every_parameter(self):
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'OK')
		self.assertEqual(self.values, self.initial_values)
		self.assertEqual(
			self.scenario.wait_state_permanence.call_count,
			len(self.scenario._build_test_cases(20, 80)),
		)

	def test_faulty_controllers_are_rejected_and_parameters_restored(self):
		for fault in (
			'frozen', 'ignore_shift', 'double_shift', 'ignore_fourth',
			'no_upper_limit', 'no_lower_limit', 'choose_before_shift', 'remember_maximum',
		):
			with self.subTest(fault=fault):
				self.fault = fault
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				self.assertEqual(self.values, self.initial_values)

	def test_request_count_mismatch_and_empty_requests_are_rejected(self):
		for circuits, expected in ((self.circuits, [40, 40]), ([], [])):
			self.assertFalse(self.scenario._requests_match(circuits, expected))
			self.assertFalse(self.scenario._check_requests(circuits, expected, 20, 80, 'invalid'))
		self.scenario._read_parameter.assert_not_called()

	def test_missing_read_or_wrong_fourth_request_is_rejected(self):
		for value in (None, 41):
			self.scenario._read_parameter.side_effect = [35, 5] * 3 + [value, 5]
			self.assertFalse(self.scenario._requests_match(self.circuits, [40] * 4))

	def test_transient_success_is_not_enough(self):
		self.scenario.wait_state_permanence.side_effect = None
		self.scenario.wait_state_permanence.return_value = False
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.values, self.initial_values)

	def test_exception_during_checks_restores_parameters(self):
		self.scenario._check_requests = Mock(side_effect=RuntimeError('simulated check failure'))
		with self.assertRaises(RuntimeError):
			self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.values, self.initial_values)

	def test_missing_initial_parameter_prevents_writes(self):
		self.scenario._read_parameter.side_effect = None
		self.scenario._read_parameter.return_value = None
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.scenario._write_parameter.assert_not_called()

	def test_restoration_continues_after_exception_or_negative_confirmation(self):
		for raises in (True, False):
			with self.subTest(raises=raises):
				self.values = self.initial_values.copy()
				def write(program_type, parameter_id, program_id, value):
					if (program_type, parameter_id, program_id) == self.restriction_key and value == 0:
						if raises:
							raise RuntimeError('simulated restoration failure')
						return False
					return self.write_parameter(program_type, parameter_id, program_id, value)
				self.scenario._write_parameter.side_effect = write
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
				for key, initial in self.initial_values.items():
					if key != self.restriction_key:
						self.assertEqual(self.values[key], initial)

	def test_partial_setup_failure_restores_parameters(self):
		def write(program_type, parameter_id, program_id, value):
			if parameter_id == snc.CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE and program_id == 102 and value == 110:
				return False
			return self.write_parameter(program_type, parameter_id, program_id, value)
		self.scenario._write_parameter.side_effect = write
		self.scenario.run()
		self.assertEqual(self.scenario._status, 'FAIL')
		self.assertEqual(self.values, self.initial_values)

	def test_invalid_ranges_fail_before_writes(self):
		for minimum, maximum in ((None, 80), (80, 20), (40, 40.1), (0, 80)):
			with self.subTest(minimum=minimum, maximum=maximum):
				boiler = self.scenario._boiler
				boiler.get_minimum_temperature.return_value = minimum
				boiler.get_maximum_temperature.return_value = maximum
				self.scenario.run()
				self.assertEqual(self.scenario._status, 'FAIL')
		self.scenario._write_parameter.assert_not_called()

	def test_cases_have_valid_flows_and_distinct_changing_winners(self):
		for minimum, maximum in ((20, 80), (10, 90), (40, 60)):
			cases = self.scenario._build_test_cases(minimum, maximum)
			for _, requests, shifts in cases:
				self.assertEqual(len(requests), 4)
				self.assertEqual(len(shifts), 4)
				for request, shift in zip(requests, shifts):
					self.assertGreaterEqual(request - shift, Scenario.TEST_MINIMUM_CONSTANT_FLOW_TEMPERATURE)
					self.assertLessEqual(request - shift, Scenario.TEST_MAXIMUM_FLOW_TEMPERATURE)
			maxima = []
			for winner, (_, requests, _) in enumerate(cases[1:5]):
				self.assertEqual(requests.index(max(requests)), winner)
				maxima.append(max(requests))
			self.assertLess(maxima[1], maxima[0])
			self.assertGreater(maxima[2], maxima[1])
			self.assertLess(maxima[3], maxima[2])
			_, requests, shifts = cases[5]
			self.assertEqual(requests.index(max(requests)), 1)
			flows = [request - shift for request, shift in zip(requests, shifts)]
			self.assertEqual(flows.index(max(flows)), 0)


if __name__ == '__main__':
	unittest.main()
"""Scenario orchestration fixtures, not a firmware or hardware integration test."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, call, patch


ROOT = Path(__file__).resolve().parents[1]


def load_modules():
	parent = ModuleType('scenario.scenario')
	parent.Scenario = type('Parent', (), {'RELAY_OFF': 0, 'RELAY_ON': 255})
	remote = ModuleType('smartnet.remoteControl')
	remote.RemoteControlParameter = Mock()
	console = ModuleType('consoleLog')
	console.print_log, console.print_error = Mock(), Mock()
	loaded = {}
	with patch.dict(sys.modules, {'scenario.scenario': parent,
		'smartnet.remoteControl': remote, 'consoleLog': console}):
		for name, path in (
			('scenario.base.district_heating', 'scenario/base/district_heating.py'),
			('scenario.base.district_heating_checks', 'scenario/base/district_heating_checks.py'),
		):
			spec = importlib.util.spec_from_file_location(name, ROOT / path)
			module = importlib.util.module_from_spec(spec)
			sys.modules[name] = module
			spec.loader.exec_module(module)
			loaded[name] = module
		for suffix in ('2', '3', '4', '5', '10_1', '10_4', '10_5', '11'):
			path = ROOT / f'scenario/list/districtHeating/scenario_district_heating_3_12_{suffix}.py'
			spec = importlib.util.spec_from_file_location(f'dh_test_{suffix}', path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
			loaded[suffix] = module
	return loaded, remote


MODULES, REMOTE = load_modules()


class TestDistrictHeatingScenarios(unittest.TestCase):
	def setUp(self):
		self.sensors = {}
		self.values = {}
		self.programs = {}
		self.writes = []
		for name, identifier in (('districtHeating', 108), ('boiler', 106),
			('circuit', 105), ('alarm', 109), ('outdoor', 107)):
			program = Mock()
			program.get_id.return_value = identifier
			parameters = {'backwardControlType': 1, 'valveRunningTime': 120,
				'currentMaximumBackwardTemperature': 40, 'maximumBackwardTemperature': 40,
				'pressureInputType': 2, 'autoFill': 1, 'fillingDuration': 60,
				'temperatureSourcePowerRequestDelay': 300, 'minimumTemperatureRestriction': 55,
				'generatorId': 108, 'heatCalculationMode': 0,
				'requiredConstantFlowTemperature': 45, 'temperatureCompensation': 5}
			self.values[name] = parameters
			program.read_parameter_value.side_effect = lambda key, p=parameters: p.get(key)
			def write(key, value, p=parameters, n=name):
				self.writes.append((n, key, value))
				if key != 'pressureLossAlarmReset':
					p[key] = value
				return True
			program.write_parameter.side_effect = write
			self.programs[name] = program
		for name in ('supply_direct_temp', 'supply_backward_temp', 'direct_temp',
			'backward_temp', 'pressure', 'outdoor'):
			sensor = Mock()
			sensor.get_value.return_value = 30
			sensor.is_mapped.return_value = True
			sensor.isManual.return_value = name == 'supply_direct_temp'
			sensor.isShort.return_value = False
			sensor.isOpen.return_value = False
			def set_value(value, manual=True, s=sensor):
				s.isShort.return_value = value == 'short'
				s.isOpen.return_value = value == 'open'
				if value not in ('short', 'open'):
					s.get_value.return_value = value
			sensor.set_value.side_effect = set_value
			self.sensors[name] = sensor
		self.programs['districtHeating'].get_input_channel.side_effect = self.sensors.__getitem__
		self.programs['alarm'].getPressure.return_value = self.sensors['pressure']
		self.programs['outdoor'].getOutdoorTemperature.return_value = self.sensors['outdoor']
		self.outputs = {name: Mock() for name in ('analog_valve', 'supply_pump', 'circulation_pump')}
		for output in self.outputs.values():
			output.is_mapped.return_value = True
		def valve_value():
			city, ret, house = [self.sensors[name].get_value() for name in
				('supply_direct_temp', 'supply_backward_temp', 'backward_temp')]
			return 0 if self.sensors['pressure'].isOpen() or ret > city or (ret > 40 and house < 40) else 254
		self.outputs['analog_valve'].get_value.side_effect = valve_value
		for name in ('supply_pump', 'circulation_pump'):
			self.outputs[name].get_value.side_effect = lambda: 0 if self.sensors['pressure'].isOpen() else 255
		self.programs['districtHeating'].get_output_channel.side_effect = self.outputs.__getitem__
		self.programs['alarm'].read_output.side_effect = lambda channel: 255 if self.sensors['pressure'].isOpen() else 0
		self.initial = {name: values.copy() for name, values in self.values.items()}

	def scenario(self, suffix):
		scenario = object.__new__(MODULES[suffix].Scenario)
		scenario._programList = dict(self.programs, weather_consumer=self.programs['circuit'])
		scenario._district_heating = self.programs['districtHeating']
		scenario._outdoor = self.programs['outdoor']
		scenario.wait = Mock(return_value=True)
		scenario.wait_until = Mock(side_effect=lambda predicate, timeout: bool(predicate()))
		scenario.wait_state_permanence = Mock(side_effect=lambda predicate, *args: bool(predicate()))
		scenario.wait_backup_generator_requested = Mock(return_value=True)
		scenario.wait_backup_generator_not_requested = Mock(return_value=True)
		return scenario

	def assert_restored(self, sensor_names):
		self.assertEqual(self.values, self.initial)
		for name in sensor_names:
			self.sensors[name].set_value.assert_called_with(30, True)
			self.sensors[name].set_manual.assert_called_with(name == 'supply_direct_temp')

	def test_valve_checks_restore_parameters_and_inputs(self):
		for suffix in ('3', '4', '5'):
			with self.subTest(scenario=suffix):
				scenario = self.scenario(suffix)
				scenario.run()
				self.assertEqual(scenario._status, 'OK')
				self.assert_restored(('supply_direct_temp', 'supply_backward_temp', 'direct_temp', 'backward_temp'))

	def test_high_house_return_keeps_city_supply_hotter(self):
		scenario = self.scenario('4')
		scenario.run()
		self.sensors['supply_direct_temp'].set_value.assert_any_call(80, True)
		self.sensors['supply_backward_temp'].set_value.assert_any_call(45, True)
		self.sensors['backward_temp'].set_value.assert_any_call(45, True)
		self.assertEqual(scenario._status, 'OK')

	def test_missing_mapping_prevents_writes(self):
		self.sensors['direct_temp'].is_mapped.return_value = False
		scenario = self.scenario('3')
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertFalse(self.writes)

	def test_initial_zero_limit_is_not_used_as_a_test_temperature(self):
		scenario = self.scenario('3')
		read = self.programs['districtHeating'].read_parameter_value.side_effect
		limits = iter((0, 40))
		self.programs['districtHeating'].read_parameter_value.side_effect = lambda name: (
			next(limits, 40) if name == 'currentMaximumBackwardTemperature' else read(name))
		base = MODULES['scenario.base.district_heating_checks']
		scenario.wait_until = base.DistrictHeatingChecks.wait_until.__get__(scenario)
		with patch.object(base.time, 'monotonic', side_effect=range(100)):
			scenario.run()
		self.assertEqual(scenario._status, 'OK')
		self.sensors['supply_backward_temp'].set_value.assert_any_call(45, True)
		self.assertNotIn(call(5, True), self.sensors['supply_backward_temp'].set_value.call_args_list)

	def test_missing_parameter_prevents_writes(self):
		self.values['districtHeating']['valveRunningTime'] = None
		scenario = self.scenario('3')
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertFalse(self.writes)

	def test_failed_cleanup_cannot_report_success(self):
		write = self.programs['districtHeating'].write_parameter.side_effect
		self.programs['districtHeating'].write_parameter.side_effect = lambda key, value: (
			False if key == 'valveRunningTime' and value == 120 else write(key, value))
		scenario = self.scenario('4')
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(self.values['districtHeating']['backwardControlType'], 1)
		self.sensors['supply_direct_temp'].set_manual.assert_called_with(True)

	def test_partial_write_failure_restores_all_settings(self):
		write = self.programs['districtHeating'].write_parameter.side_effect
		self.programs['districtHeating'].write_parameter.side_effect = lambda key, value: (
			False if key == 'valveRunningTime' and value == 30 else write(key, value))
		scenario = self.scenario('3')
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assertEqual(self.values, self.initial)

	def test_timeout_and_cancellation_restore_conditions(self):
		for failing_method in ('wait_until', 'wait'):
			with self.subTest(method=failing_method):
				scenario = self.scenario('3')
				setattr(scenario, failing_method, Mock(return_value=False))
				scenario.run()
				self.assertEqual(scenario._status, 'FAIL')
				self.assert_restored(('supply_direct_temp', 'supply_backward_temp', 'direct_temp', 'backward_temp'))

	def test_alarm_polarity_and_confirmed_state(self):
		for suffix in ('10_1', '11'):
			with self.subTest(scenario=suffix):
				scenario = self.scenario(suffix)
				scenario.run()
				self.assertEqual(scenario._status, 'OK')
				self.assertIn(('alarm', 'pressureInputType', 0), self.writes)
				calls = self.sensors['pressure'].set_value.call_args_list
				self.assertLess(calls.index(call('short', True)), calls.index(call('open', True)))
				self.assert_restored(('pressure',))

	def test_unconfirmed_alarm_does_not_test_reserve(self):
		self.programs['alarm'].read_output.return_value = 0
		self.programs['alarm'].read_output.side_effect = None
		scenario = self.scenario('10_1')
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		scenario.wait_backup_generator_requested.assert_not_called()
		self.assert_restored(('pressure',))

	def test_failed_alarm_response_resets_latch_before_restoring_autofill(self):
		scenario = self.scenario('11')
		scenario.wait_state_permanence.return_value = False
		scenario.wait_state_permanence.side_effect = None
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		reset = self.writes.index(('alarm', 'pressureLossAlarmReset', 0))
		restore = self.writes.index(('alarm', 'autoFill', 1))
		self.assertLess(reset, restore)
		self.assert_restored(('pressure',))
		self.assertFalse(self.sensors['pressure'].isOpen())

	def test_failed_alarm_reset_prevents_success_but_still_restores_settings(self):
		write = self.programs['alarm'].write_parameter.side_effect
		self.programs['alarm'].write_parameter.side_effect = lambda key, value: (
			False if key == 'pressureLossAlarmReset' else write(key, value))
		scenario = self.scenario('11')
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assert_restored(('pressure',))

	def test_no_consumer_check_creates_a_cold_city_source(self):
		scenario = self.scenario('10_4')
		scenario.run()
		self.assertEqual(scenario._status, 'OK')
		self.sensors['supply_direct_temp'].set_value.assert_any_call(25, True)
		self.sensors['supply_backward_temp'].set_value.assert_any_call(30, True)
		self.assertIn(('circuit', 'generatorId', 107), self.writes)
		self.assert_restored(('supply_direct_temp', 'supply_backward_temp', 'direct_temp', 'backward_temp'))

	def test_cold_house_check_restores_warm_not_initial_temperature(self):
		scenario = self.scenario('10_5')
		scenario.read_temperature_source_required_temperature = Mock(return_value=50)
		scenario.run()
		self.assertEqual(scenario._status, 'OK')
		calls = self.sensors['direct_temp'].set_value.call_args_list
		self.assertLess(calls.index(call(40, True)), len(calls) - 2)
		self.assertEqual(calls[-2], call(55, True))
		self.assert_restored(('supply_direct_temp', 'supply_backward_temp', 'direct_temp', 'backward_temp'))

	def test_retained_reserve_remains_a_failure(self):
		scenario = self.scenario('10_5')
		scenario.read_temperature_source_required_temperature = Mock(return_value=50)
		scenario.wait_backup_generator_not_requested.side_effect = [True, False]
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assert_restored(('direct_temp',))

	def test_weather_reads_receiver_parameter_without_echo(self):
		parameter = Mock()
		parameter.get_value.return_value = -5
		with patch.object(MODULES['2'].sr, 'RemoteControlParameter', return_value=parameter) as remote:
			scenario = self.scenario('2')
			self.assertEqual(scenario.read_filtered_outdoor_temperature(-5), -5)
			self.assertEqual(remote.call_args.kwargs['programId'], 105)
			parameter.read.assert_called_once()

	def test_weather_failure_restores_auto_mode_and_sensor(self):
		scenario = self.scenario('2')
		scenario.read_maximum_backward_temperature_ii = Mock(return_value=90)
		scenario.read_outdoor_temperature_ii = Mock(return_value=0)
		scenario.read_filtered_outdoor_temperature = Mock(return_value=None)
		scenario.run()
		self.assertEqual(scenario._status, 'FAIL')
		self.assert_restored(('outdoor',))


if __name__ == '__main__':
	unittest.main()
"""Ventilation plant checks: no GUI, controller, CAN, or wall-clock sleeps."""

import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

# Match application startup: the legacy message/mainThread imports are cyclic.
import mainThread
from presets.preset import ProgramPreset, validate_program_presets
from presets.settings import RoomSettings
from presets.ventilation import make_presets, ROOM_ID, CIRCUIT_ID, VENTILATION_ID
from programs.factory import createProgram, programCreator
from programs.program import Program
from programs.room import Room
from programs.ventilation import Ventilation
from simulator.heating_circuit import Simulator as CircuitSimulator
from simulator.room import Simulator as RoomSimulator
from simulator.simulator import Simulator as PlantSimulator, simulatorType
from simulator.ventilation import Simulator, AIR_CAPACITY, WATER_CAPACITY, thermal_step
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


class VentilationTests(unittest.TestCase):
	def setUp(self):
		self.clock = 0.0
		self.outdoor_temperature = -10.0
		clock = patch('simulator.ventilation.time.monotonic', side_effect=lambda: self.clock)
		clock.start()
		self.addCleanup(clock.stop)
		# Output initialization normally reads the actual controller.
		read = patch.object(Program, 'read_output', return_value=0)
		read.start()
		self.addCleanup(read.stop)
		self.make_plant()

	def make_plant(self, supply_exhaust=True, analog=True):
		presets, _ = make_presets(supply_exhaust, analog)
		self.programs = {preset.get_type(): createProgram(preset) for preset in presets}
		for program in self.programs.values():
			self.addCleanup(program.clear)
		self.control = SimpleNamespace(
			getOat=lambda: SimpleNamespace(get_temperature=lambda: self.outdoor_temperature),
			_collector=SimpleNamespace(get_direct_temperature=lambda: 80.0),
		)
		self.room_program = self.programs[snc.ProgramType.ROOM_DEVICE]
		self.circuit_program = self.programs[snc.ProgramType.HEATING_CIRCUIT]
		self.program = self.programs[snc.ProgramType.VENTILATION]
		self.room = RoomSimulator(self.room_program, self.control)
		self.circuit = CircuitSimulator(self.circuit_program, self.control)
		self.model = Simulator(self.program, self.control)
		self.control.getHeatingCircuitList = lambda: [self.circuit]
		self.control._roomList = [self.room]
		self.control._heatingCircuitList = [self.circuit]
		self.control._ventilation_list = [self.model]
		self.control._simList = [self.room, self.model, self.circuit]
		PlantSimulator._bind_ventilation(self.control)
		self.set_output('fan_enable', 255)
		self.set_output('supply_fan', 254)
		self.set_output('exhaust_fan', 254)
		self.set_output('outer_shutter', 254)
		self.set_output('mixer_shutter', 0)
		self.set_output('discrete_outer_shutter', 255)
		self.set_output('discrete_mixer_shutter', 0)
		self.circuit_program.set_output_value('pump', 255)
		self.circuit_program.set_output_value('analogValve', 254)
		self.circuit.set_temperature(60.0)

	def set_output(self, name, value):
		self.program.set_output_value(name, value)

	def parameter(self, name, value):
		self.program.get_parameters()[name].set_value(value)

	def advance(self, elapsed, update_room=False):
		self.clock += elapsed
		self.model.run()
		if update_room:
			self.room.run()

	def test_indexes_and_registration(self):
		self.assertIs(programCreator[snc.ProgramType.VENTILATION], Ventilation)
		self.assertIs(simulatorType[snc.ProgramType.VENTILATION], Simulator)
		self.assertEqual([channel.get_id() for channel in self.program.get_inputs().values()], list(range(4)))
		self.assertEqual([channel.get_id() for channel in self.program.get_outputs().values()], list(range(9)))
		self.assertEqual(self.control._simList, [self.circuit, self.model, self.room])

	def test_analog_fans_common_enable_and_relay_on(self):
		for value, expected in ((0, 0), (127, 0.5), (254, 1), (255, 1), (None, 0), (float('nan'), 0)):
			self.set_output('supply_fan', value)
			self.assertEqual(self.model.fan_speed('supply_fan'), expected)
		self.set_output('fan_enable', 0)
		self.assertEqual(self.model.fan_speed('supply_fan'), 0)

	def test_analog_only_discrete_only_and_external_fans(self):
		analog = self.program.get_output_channel('supply_fan')
		discrete = self.program.get_output_channel('fan_enable')
		discrete.set_mapping(None)
		self.set_output('supply_fan', 127)
		self.assertEqual(self.model.fan_speed('supply_fan'), 0.5)
		analog.set_mapping(None)
		self.assertEqual(self.model.fan_speed('supply_fan'), 1)
		discrete.set_mapping(ChannelMapping(0, 'CHANNEL_RELAY', 123))
		for value, expected in ((0, 0), (1, 1), (255, 1), (None, 0)):
			self.set_output('fan_enable', value)
			self.assertEqual(self.model.fan_speed('supply_fan'), expected)

	def test_shutter_priority_and_undefined_mapping(self):
		self.set_output('outer_shutter', 127)
		self.set_output('discrete_outer_shutter', 0)
		self.assertEqual(self.model.shutter_position('outer_shutter', 'discrete_outer_shutter'), 0.5)
		self.program.get_output_channel('outer_shutter').set_mapping(None)
		channel = self.program.get_output_channel('discrete_outer_shutter')
		channel.set_mapping(ChannelMapping(0, 'CHANNEL_RELAY', 123))
		self.assertEqual(self.model.shutter_position('outer_shutter', 'discrete_outer_shutter'), 0)
		channel.set_mapping(ChannelMapping(0, 'CHANNEL_UNDEFINED', 0))
		self.assertEqual(self.model.shutter_position('outer_shutter', 'discrete_outer_shutter'), 1)

	def test_mixing_and_total_flow_limit(self):
		full_flow = self.model.parameter('air_flow') / 3600
		self.set_output('outer_shutter', 127)
		self.set_output('mixer_shutter', 127)
		fresh, recirculated = self.model.air_flows()
		self.assertAlmostEqual(fresh, full_flow / 2)
		self.assertAlmostEqual(recirculated, full_flow / 2)
		self.set_output('outer_shutter', 254)
		self.set_output('mixer_shutter', 254)
		self.assertAlmostEqual(sum(self.model.air_flows()), full_flow)
		self.set_output('exhaust_fan', 0)
		self.assertEqual(self.model.air_flows(), (full_flow, 0))

	def test_supply_scheme_ignores_exhaust_and_mixer(self):
		self.make_plant(supply_exhaust=False)
		self.set_output('outer_shutter', 0)
		self.set_output('mixer_shutter', 254)
		self.assertEqual(self.model.air_flows(), (0, 0))
		self.set_output('outer_shutter', 127)
		self.assertAlmostEqual(sum(self.model.air_flows()), self.model.parameter('air_flow') / 7200)

	def test_discrete_scheme_and_missing_heater(self):
		self.make_plant(analog=False)
		self.set_output('discrete_outer_shutter', 0)
		self.set_output('discrete_mixer_shutter', 255)
		self.assertEqual(self.model.air_flows()[0], 0)
		self.assertGreater(self.model.air_flows()[1], 0)
		self.set_output('heater', 255)  # Unmapped output must not heat.
		self.assertEqual(self.model.output('heater'), 0)

	def test_warm_water_heats_air_and_return_is_below_supply(self):
		self.advance(1200)
		self.assertGreater(self.model.get_return_temperature(), 20)
		self.assertLess(self.model.get_return_temperature(), 60)
		self.assertGreater(self.model.get_temperature(), self.outdoor_temperature)
		self.assertGreater(self.model.get_water_power(), 0)
		self.assertAlmostEqual(self.circuit.get_power(), self.model.get_water_power())

	def test_water_energy_balance_includes_coil_storage(self):
		old_water = self.model.get_return_temperature()
		elapsed = 60
		self.advance(elapsed)
		water_capacity_rate = self.circuit.get_max_flow_rate() / 3600 * WATER_CAPACITY
		mean_water = 60 - self.model.get_water_power() * 1000 / water_capacity_rate
		air_capacity_rate = sum(self.model.air_flows()) * AIR_CAPACITY
		conductance = air_capacity_rate * -math.expm1(-self.model.parameter('coil_conductance') / air_capacity_rate)
		conductance = min(conductance, self.circuit.get_max_power() * 1000 / (old_water - self.outdoor_temperature))
		air_energy = conductance * (mean_water - self.outdoor_temperature) * elapsed
		stored = (self.model.get_return_temperature() - old_water) * self.model.parameter('coil_capacity') * 1000
		self.assertAlmostEqual(self.model.get_water_power() * 1000 * elapsed, stored + air_energy)

	def test_no_water_circulation_cools_return_towards_freezing(self):
		self.circuit_program.set_output_value('pump', 0)
		self.advance(3600)
		self.assertLess(self.model.get_return_temperature(), 0)
		self.assertEqual(self.model.get_water_power(), 0)
		self.assertEqual(self.circuit.get_power(), 0)

	def test_recirculation_is_warmer_than_fresh_air(self):
		self.circuit_program.set_output_value('pump', 0)
		self.advance(600)
		fresh_temperature = self.model.get_temperature()
		self.set_output('outer_shutter', 0)
		self.set_output('mixer_shutter', 254)
		self.advance(600)
		self.assertGreater(self.model.get_temperature(), fresh_temperature)

	def test_electric_heater_and_safe_zero_airflow(self):
		self.circuit_program.set_output_value('pump', 0)
		self.set_output('fan_enable', 0)
		self.set_output('heater', 255)
		self.parameter('electric_power', 30)
		self.advance(86400)
		self.assertTrue(math.isfinite(self.model.get_temperature()))
		self.assertGreater(self.model.get_temperature(), 20)
		self.assertLess(self.model.get_temperature(), 1000)
		# The physical plant can overheat beyond the sensor's measurement range.
		self.assertEqual(self.program.get_input_channel('air_temperature').get_value(), 120)
		self.assertEqual(self.model._air_flow, 0)

	def test_fresh_air_dries_room_but_recirculation_does_not(self):
		self.room_program.get_parameters()['humidity_generation'].set_value(0)
		self.advance(600)
		self.assertLess(self.model.room_humidity(50), 50)
		self.assertGreater(self.model.room_humidity(50), self.model.parameter('outdoor_humidity'))
		self.set_output('outer_shutter', 0)
		self.set_output('mixer_shutter', 254)
		self.advance(600)
		self.assertEqual(self.model.room_humidity(50), 50)
		self.set_output('fan_enable', 0)
		self.advance(600)
		self.assertEqual(self.model.room_humidity(50), 50)

	def test_humidity_generation_and_bounds(self):
		self.set_output('fan_enable', 0)
		self.advance(3600)
		self.assertEqual(self.model.room_humidity(50), 51)
		self.assertEqual(self.model.room_humidity(100), 100)
		self.room_program.get_parameters()['humidity_generation'].set_value(0)
		self.set_output('fan_enable', 255)
		self.advance(86400)
		self.assertGreaterEqual(self.model.room_humidity(50), 0)

	def test_room_heat_depends_on_air_not_direct_third_circuit(self):
		self.assertEqual(self.room.getAdditionalSourceTemperature(), self.room.get_temperature())
		self.assertEqual(self.room.getAdditionalSourcePower(), 0)
		self.advance(60)
		self.assertGreater(self.model.room_temperature_change(-10), 0)
		self.assertLess(self.model.room_temperature_change(80), 0)
		self.set_output('fan_enable', 0)
		self.advance(60)
		self.assertEqual(self.model.room_temperature_change(20), 0)
		self.room._ventilation = None
		self.model._water_power = 1
		self.assertEqual(self.room.getAdditionalSourceTemperature(), 60)
		self.assertEqual(self.room.getAdditionalSourcePower(), 1)

	def test_manual_inputs_and_alarm_contacts_survive_steps(self):
		for name, value in (('return_temperature', 3), ('air_temperature', 65)):
			channel = self.program.get_input_channel(name)
			channel.set_manual(True)
			channel.set_value(value, manual=True)
		for name in ('filter', 'fire_alarm'):
			self.program.get_input_channel(name).set_value('short')
		for name, value in (('roomTemperature', 24), ('humidity', 75)):
			channel = self.room_program.get_input_channel(name)
			channel.set_manual(True)
			channel.set_value(value, manual=True)
		self.advance(60, update_room=True)
		self.assertEqual(self.program.get_input_channel('return_temperature').get_value(), 3)
		self.assertEqual(self.program.get_input_channel('air_temperature').get_value(), 65)
		self.assertEqual(self.room.get_temperature(), 24)
		self.assertEqual(self.room_program.get_input_channel('humidity').get_value(), 75)
		self.assertTrue(self.program.get_input_channel('filter').isShort())
		self.assertTrue(self.program.get_input_channel('fire_alarm').isShort())

	def test_auto_sensor_fault_flags_are_not_overwritten(self):
		channel = self.program.get_input_channel('return_temperature')
		channel.set_value('open')
		self.advance(60)
		self.assertTrue(channel.isOpen())

	def test_repeat_at_same_time_is_idempotent(self):
		self.advance(60)
		before = self.model.get_temperature(), self.model.get_return_temperature()
		self.advance(0)
		self.assertEqual(before, (self.model.get_temperature(), self.model.get_return_temperature()))

	def test_circuit_uses_coil_return_and_other_circuit_keeps_legacy_load(self):
		self.advance(120)
		self.assertEqual(self.circuit.compute_backward_temperature2(), self.model.get_return_temperature())
		self.circuit._ventilation_load = None
		self.assertEqual(self.circuit.get_power(), self.circuit.get_max_power())
		self.assertNotEqual(self.circuit.compute_backward_temperature2(), self.model.get_return_temperature())

	def test_full_plant_ticks_and_room_outputs(self):
		for _ in range(120):
			self.clock += 1
			for model in self.control._simList:
				model.run()
		self.assertGreater(self.model.get_return_temperature(), 20)
		self.assertLess(self.room_program.get_input_channel('humidity').get_value(), 50)
		self.assertTrue(math.isfinite(self.room.get_temperature()))

	def test_missing_room_and_multiple_rooms_are_rejected(self):
		for rooms in ([], [self.room, self.room]):
			with self.assertRaisesRegex(ValueError, 'exactly one room'):
				self.model.bind(rooms, [self.circuit])

	def test_missing_circuit_or_required_sensors_are_rejected(self):
		with self.assertRaisesRegex(ValueError, 'RESPONSIBLE_CIRCUIT_3'):
			self.model.bind([self.room], [])
		for name in ('return_temperature', 'air_temperature'):
			channel = self.program.get_input_channel(name)
			mapping = channel.get_mapping()
			channel.set_mapping(None)
			with self.assertRaisesRegex(ValueError, 'required sensor'):
				self.model.bind([self.room], [self.circuit])
			channel.set_mapping(mapping)

	def test_shared_coil_and_unknown_ventilation_are_rejected(self):
		with self.assertRaisesRegex(ValueError, 'more than one ventilation'):
			self.circuit.set_ventilation_load(object())
		self.control._ventilation_list = []
		with self.assertRaisesRegex(ValueError, 'does not exist'):
			PlantSimulator._bind_ventilation(self.control)

	def test_presets_settings_schemes_and_optional_sensors(self):
		for supply_exhaust in (False, True):
			for analog in (False, True):
				presets, controllers = make_presets(supply_exhaust, analog)
				validate_program_presets(presets)
				self.assertEqual([controller.get_id() for controller in controllers], [123, 124, 125])
				room = next(p for p in presets if p.get_id() == ROOM_ID)
				values = {p.get_parameter_id(): p.get_value() for p in room.getSettings().get()}
				self.assertEqual(values[snc.RoomDeviceParameterId.VENTILATION_CIRCUIT], VENTILATION_ID)
				self.assertEqual(values[snc.RoomDeviceParameterId.RESPONSIBLE_CIRCUIT_3], CIRCUIT_ID)
				vent = next(p for p in presets if p.get_id() == VENTILATION_ID)
				self.assertTrue(vent.get_inputs()[1] and vent.get_inputs()[2])
				self.assertEqual([(mapping.get_host_id(), mapping.get_channel_id())
					for mapping in vent.get_inputs()[1:3]], [(125, 0), (125, 1)])
				self.assertEqual(vent.get_inputs()[0] is not None, supply_exhaust)
				self.assertEqual(vent.get_inputs()[3] is not None, supply_exhaust)
		self.program.set_scheme(1)
		self.assertTrue(self.program.is_supply_exhaust())
		self.program.set_scheme('DEFAULT')
		self.assertFalse(self.program.is_supply_exhaust())
		self.program.set_scheme(99)
		with self.assertRaises(ValueError):
			self.program.is_supply_exhaust()

	def test_all_preset_channels_fit_declared_controllers(self):
		from controllers.controller_io import ControllerIO

		for supply_exhaust in (False, True):
			for analog in (False, True):
				with self.subTest(supply_exhaust=supply_exhaust, analog=analog):
					presets, controller_presets = make_presets(supply_exhaust, analog)
					controllers = {}
					with patch('controllers.controller_io.sm.Message.send'):
						for preset in controller_presets:
							controller = ControllerIO(preset.get_id(), preset.get_type(), preset.get_title())
							self.addCleanup(controller.clear)
							controllers[controller.get_id()] = controller
					used_channels = set()
					for program in presets:
						for kind, mappings in (('input', program.get_inputs()), ('output', program.get_outputs())):
							for mapping in mappings:
								if mapping is None:
									continue
								controller = controllers[mapping.get_host_id()]
								validate = (controller.validate_input_channel if kind == 'input'
									else controller.validate_output_channel)
								validate(mapping.get_channel_id())
								channel = (kind, mapping.get_host_id(), mapping.get_channel_id())
								self.assertNotIn(channel, used_channels)
								used_channels.add(channel)

	def test_empty_room_settings_and_legacy_settings_are_supported(self):
		preset = ProgramPreset(snc.ProgramType.ROOM_DEVICE, 'DEFAULT', 99, 'empty', None, [], [])
		room = Room(preset)
		self.addCleanup(room.clear)
		self.assertEqual(room.getRoomTemperatureSourceList(), [0, 0, 0])
		self.assertEqual(room.get_ventilation_id(), 0)
		self.assertEqual(len(RoomSettings().get()), 3)

	def test_thermal_step_is_stable(self):
		self.assertEqual(thermal_step(20, -10, 0, 1, 10), 20)
		self.assertEqual(thermal_step(20, -10, 100, 1, 0), 20)
		self.assertEqual(thermal_step(20, -10, 100, 1, 10000), -10)


if __name__ == '__main__':
	unittest.main()
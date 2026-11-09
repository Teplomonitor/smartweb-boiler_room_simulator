"""Physical plant only: scheduling, alarms and protections belong to SmartWeb.

Humidity is a simplified percentage tracer, not a psychrometric model. Water
and duct temperatures have finite heat capacities, including at zero airflow.
"""

import math
import time

from functions.limit import limit


AIR_CAPACITY = 1.2 * 1005.0  # J/(m³ K)
WATER_CAPACITY = 4200.0  # J/(kg K)
RELAY_MAX = 254.0  # 255 (RELAY_ON) also means fully on.
NATURAL_COIL_CONDUCTANCE = 3.0  # W/K, stagnant air near the coil
DUCT_LOSS_CONDUCTANCE = 8.0  # W/K, duct to surrounding room
DUCT_RADIATION = 0.8 * 2.0 * 5.670374419e-8  # emissivity * area (m²) * Stefan-Boltzmann
KELVIN_OFFSET = 273.15


def finite_value(value, default=0.0):
	if isinstance(value, (int, float)) and math.isfinite(value):
		return float(value)
	return default


def thermal_step(current, target, conductance, capacity, elapsed):
	"""Exact first-order step; stable even after a delayed simulation tick."""
	if conductance <= 0 or elapsed <= 0:
		return current
	return target + (current - target) * math.exp(-conductance * elapsed / capacity)


class Simulator:
	def __init__(self, program, control):
		self._program = program
		self._control = control
		self._room = None
		self._circuit = None
		self._supply_exhaust = program.is_supply_exhaust()
		self._return_temperature = 20.0
		self._air_temperature = 20.0
		self._water_power = 0.0
		self._air_flow = 0.0
		self._fresh_flow = 0.0
		self._elapsed = 0.0
		self._last_update = time.monotonic()
		for name in ('return_temperature', 'air_temperature'):
			self.publish_temperature(name, 20.0)
		# These contacts stay available for manual fault injection. Never reset
		# them in run(): doing so would erase a simulated fire/filter event.
		for name in ('filter', 'fire_alarm'):
			channel = program.get_input_channel(name)
			if channel.is_mapped() and channel.isAuto() and not channel.isShort() and not channel.isOpen():
				channel.set_value('open')

	def bind(self, rooms, circuits):
		linked = [room for room in rooms
			if room._program.get_ventilation_id() == self._program.get_id()]
		if len(linked) != 1:
			raise ValueError(f'Ventilation {self._program.get_id()} requires exactly one room; found {len(linked)}')
		room = linked[0]
		circuit_id = room._program.getRoomTemperatureSourceList()[2]
		circuit = next((item for item in circuits if item._program.get_id() == circuit_id), None)
		if not circuit_id or circuit is None:
			raise ValueError(f'Ventilation {self._program.get_id()}: invalid RESPONSIBLE_CIRCUIT_3={circuit_id}')
		for name in ('return_temperature', 'air_temperature'):
			if not self._program.get_input_channel(name).is_mapped():
				raise ValueError(f'Ventilation {self._program.get_id()}: required sensor {name} is not mapped')
		circuit.set_ventilation_load(self)
		room.set_ventilation(self)
		self._room, self._circuit = room, circuit

	def parameter(self, name):
		parameter = self._program.get_parameters()[name]
		return limit(parameter.getMin(), finite_value(parameter.get_value(), parameter.getMin()), parameter.getMax())

	def output(self, name, analog=False, unmapped=0.0):
		channel = self._program.get_output_channel(name)
		if not channel.is_mapped():
			return unmapped
		value = finite_value(channel.get_value())
		return limit(0.0, value / RELAY_MAX, 1.0) if analog else float(value > 0)

	def fan_speed(self, name):
		analog = self._program.get_output_channel(name).is_mapped()
		discrete = self._program.get_output_channel('fan_enable').is_mapped()
		# SmartWeb assumes external operation if neither output is mapped.
		if not analog and not discrete:
			return 1.0
		enabled = self.output('fan_enable', unmapped=1.0)
		return enabled * self.output(name, analog=True, unmapped=1.0)

	def shutter_position(self, analog, discrete):
		if self._program.get_output_channel(analog).is_mapped():
			return self.output(analog, analog=True)
		return self.output(discrete, unmapped=1.0)

	def air_flows(self):
		"""Return fresh and recirculated volume flows, in m³/s."""
		supply = self.fan_speed('supply_fan') * self.parameter('air_flow') / 3600.0
		outer = self.shutter_position('outer_shutter', 'discrete_outer_shutter')
		fresh = supply * outer
		recirculated = 0.0
		if self._supply_exhaust:
			exhaust = self.fan_speed('exhaust_fan') * self.parameter('air_flow') / 3600.0
			mixer = self.shutter_position('mixer_shutter', 'discrete_mixer_shutter')
			recirculated = min(supply, exhaust) * mixer
		# Two independently open branches cannot exceed fan capacity.
		total = fresh + recirculated
		if total > supply and total > 0:
			fresh *= supply / total
			recirculated *= supply / total
		return fresh, recirculated

	def get_return_temperature(self):
		return self._return_temperature

	def get_water_power(self):
		return self._water_power

	def get_temperature(self):
		return self._air_temperature

	def publish_temperature(self, name, value):
		channel = self._program.get_input_channel(name)
		if not channel.isShort() and not channel.isOpen():
			# Retain fault injection and respect both manual mode and sensor range.
			channel.set_value(limit(channel.getMin(), value, channel.getMax()))

	def update_duct_temperature(self, inlet, room_temperature, air_conductance, power):
		# Implicit energy balance including radiation. The residual is monotonic
		# above absolute zero, so bisection remains stable for arbitrarily long ticks.
		storage = self.parameter('duct_capacity') * 1000.0 / self._elapsed
		conductance = storage + air_conductance + DUCT_LOSS_CONDUCTANCE
		source = (storage * self._air_temperature + air_conductance * inlet
			+ DUCT_LOSS_CONDUCTANCE * room_temperature + power)
		room_kelvin = max(0.0, room_temperature + KELVIN_OFFSET)

		def residual(temperature):
			return (conductance * temperature - source
				+ DUCT_RADIATION * ((temperature + KELVIN_OFFSET)**4 - room_kelvin**4))

		low = -KELVIN_OFFSET
		high = max(self._air_temperature, inlet, room_temperature, source / conductance)
		for _ in range(64):
			middle = (low + high) / 2
			if residual(middle) > 0:
				high = middle
			else:
				low = middle
		self._air_temperature = (low + high) / 2

	def run(self):
		now = time.monotonic()
		self._elapsed = max(0.0, now - self._last_update)
		self._last_update = now
		air_channel = self._program.get_input_channel('air_temperature')
		if air_channel.isManual():
			# Manual input is a scenario override of the physical temperature.
			# Open/short only affects measurement, never this physical state.
			self._air_temperature = finite_value(air_channel.get_value(), self._air_temperature)
		if self._room is None or self._elapsed == 0:
			return
		room_temperature = finite_value(self._room.get_temperature(), 20.0)
		oat = self._control.getOat()
		outdoor = finite_value(oat.get_temperature(), 0.0) if oat is not None else 0.0
		fresh, recirculated = self.air_flows()
		self._fresh_flow = fresh
		self._air_flow = fresh + recirculated
		outer = self.shutter_position('outer_shutter', 'discrete_outer_shutter')
		inlet = ((fresh * outdoor + recirculated * room_temperature) / self._air_flow
			if self._air_flow > 0 else outer * outdoor + (1 - outer) * room_temperature)
		air_conductance = self._air_flow * AIR_CAPACITY
		coil_conductance = (air_conductance * -math.expm1(-self.parameter('coil_conductance') / air_conductance)
			if air_conductance > 0 else NATURAL_COIL_CONDUCTANCE)
		water_conductance = (max(0.0, finite_value(self._circuit.get_max_flow_rate()))
			/ 3600.0 * WATER_CAPACITY * self._circuit.get_pump_state())
		supply = finite_value(self._circuit.get_temperature(), room_temperature)
		# max_power describes the installed coil rating, not a controller command.
		delta = abs(self._return_temperature - inlet)
		if delta > 0 and air_conductance > 0:
			coil_conductance = min(coil_conductance,
				max(0.0, finite_value(self._circuit.get_max_power())) * 1000 / delta)
		total = water_conductance + coil_conductance
		target = (water_conductance * supply + coil_conductance * inlet) / total if total else self._return_temperature
		old_return = self._return_temperature
		capacity = self.parameter('coil_capacity') * 1000.0
		self._return_temperature = thermal_step(old_return, target, total, capacity, self._elapsed)
		# Mean water temperature gives the mean transferred energy over this step.
		x = total * self._elapsed / capacity
		mean_return = target + (old_return - target) * (-math.expm1(-x) / x) if x > 0 else old_return
		self._water_power = water_conductance * (supply - mean_return) / 1000.0
		coil_power = coil_conductance * (mean_return - inlet)
		electric_power = self.output('heater') * self.parameter('electric_power') * 1000.0
		# Stagnant air still heats up; never suppress a bad controller command.
		if air_channel.isAuto():
			self.update_duct_temperature(inlet, room_temperature, air_conductance, coil_power + electric_power)
		self.publish_temperature('return_temperature', self._return_temperature)
		self.publish_temperature('air_temperature', self._air_temperature)

	def room_temperature_change(self, temperature):
		capacity = self._room._program.get_parameters()['thermal_capacity'].get_value() * 1000.0
		capacity = max(1000.0, finite_value(capacity, 3000000.0))
		return thermal_step(temperature, self._air_temperature,
			self._air_flow * AIR_CAPACITY, capacity, self._elapsed) - temperature

	def room_humidity(self, humidity):
		parameters = self._room._program.get_parameters()
		volume = max(1.0, finite_value(parameters['volume'].get_value(), 150.0))
		generation = max(0.0, finite_value(parameters['humidity_generation'].get_value())) / 3600.0
		rate = self._fresh_flow / volume
		outdoor = self.parameter('outdoor_humidity')
		# Deliberately simplified: temperature alone does not change this tracer.
		if rate > 0:
			humidity = thermal_step(humidity, outdoor + generation / rate, rate, 1.0, self._elapsed)
		else:
			humidity += generation * self._elapsed
		return limit(0.0, humidity, 100.0)
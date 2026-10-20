
import time
from functions.timeOnOffDelay import TimeOnOffDelay as TimeOnOffDelay
from functions.limit import limit

BROADCAST_ID = 0

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.get_preset()
		self._time_start    = time.time()
		self._control    = control
		self._currentPower = 0
		self._discrete_power = 0
		
		self._boilerOverheatDelay = TimeOnOffDelay()
		

		self._tMax = 75
		self._tMin = 20
		self.set_temperature(30)

	def get_supply_backward_temperature(self):
		return self._control._collector.get_supply_backward_temperature()
	
	def get_temperature(self):
		return self._program.get_temperature()

	def set_temperature(self, value):
#		print(f'boiler: {value}')
		self._program.set_temperature(value)

	def get_elapsed_time(self):
		return time.time() - self._time_start

	def get_consumer_power(self):
		consumersPower = self._control.get_consumer_power(self._program.get_id())
		return consumersPower

	def get_stage_state(self):
		stage = self._program.get_stage_1()
		if stage.is_mapped() is False:
			return 0

		if stage.get_value():
			return 1

		return 0
	
	def get_pump_state(self):
		pumpState = self._program.get_pump()
		if pumpState.is_mapped() is False:
			return 1

		if pumpState.get_value():
			return 1

		return 0
		
	
	def get_max_power(self):
		return self._program.get_max_power()
	
	def compute_power(self):
		discrete_target = sum(power for stage, power in (
			(self._program.get_stage_1(), self._program.get_stage_1_power()),
			(self._program.get_stage_2(), self._program.get_stage_2_power()),
		) if stage.is_mapped() and stage.get_value())

		# Preserve the existing discrete burner temperature characteristic.
		temperature_fraction = limit(0, (self.get_temperature() - (self._tMax - 20)) / 20, 1)
		discrete_target *= 1 - 0.4 * temperature_fraction

		modulation = self._program.get_power_output_percent()
		fraction = 0 if modulation is None else limit(0, modulation / 100, 1)
		analog_power = self._program.get_analog_power() * fraction

		if self._boilerOverheatDelay.get(self.get_temperature() > self._tMax, 30, 30):
			discrete_target = 0
			analog_power = 0

		# Keep the legacy ramp rates (kW per simulation tick), also in mixed mode.
		if self._discrete_power < discrete_target:
			self._discrete_power = min(discrete_target, self._discrete_power + 0.05)
		else:
			self._discrete_power = max(discrete_target, self._discrete_power - 0.5)
		self._currentPower = self._discrete_power + analog_power

	def compute_modulating_power(self):
		# Compatibility entry point; all combinations use the same power model.
		self.compute_power()
			
	def get_power(self):
		return self._currentPower

	def get_max_flow_rate(self):
		return self._program.get_max_flow_rate()
	
	def get_flow(self):
		if self.get_pump_state():
			return self.get_max_flow_rate() / 1000 # cube per hour
		return 0
		
	def get_cooldown_power(self):
		dt = self.get_temperature() - self._tMin
		return dt/self._tMax

	def get_total_power(self):
		return self.get_power() - self.get_cooldown_power()

	def compute_temperature(self):
		flow = self.get_flow()
		direct_temp = self.get_temperature()
		if flow:
			temp = self.get_supply_backward_temperature()
		else:
			temp = direct_temp
			
		
		if flow:
			k = 0.9
			dt = self.get_total_power() / flow * k
		else:
			dt = self.get_total_power() * 0.5
		
		temp = limit(direct_temp - 1, temp + dt, direct_temp + 1) # don't want temp grow too fast
		
		temp = limit(self._tMin, temp, self._tMax + 10)

#		print(f'b{self._program.get_id()} t = {temp}')
		
		return temp

	def run(self):
		self.set_temperature(self.compute_temperature())
		self.compute_power()


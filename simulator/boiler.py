
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
		
		self._boilerOverheatDelay = TimeOnOffDelay()
		

		self._tMax = 75
		self._tMin = 20
		self.set_temperature(30)

	def getSupplyBackwardTemperature(self):
		return self._control._collector.getSupplyBackwardTemperature()
	
	def get_temperature(self):
		return self._program.get_temperature()

	def set_temperature(self, value):
#		print(f'boiler: {value}')
		self._program.set_temperature(value)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getConsumersPower(self):
		consumersPower = self._control.getConsumersPower(self._program.get_id())
		return consumersPower

	def getStageState(self):
		stage = self._program.get_stage_1()
		if stage.isMapped() is False:
			return 1

		if stage.get_value():
			return 1

		return 0
	
	def getPumpState(self):
		pumpState = self._program.get_pump()
		if pumpState.isMapped() is False:
			return 1

		if pumpState.get_value():
			return 1

		return 0
		
	
	def get_max_power(self):
		return self._program.get_max_power()
	
	def computePower(self):	
		if self.getStageState():
			offset = 20
			temp = self.get_temperature()

			overheatOnDelay  = 30
			overheatOffDelay = 30
			
			if self._boilerOverheatDelay.get(temp > self._tMax, overheatOnDelay, overheatOffDelay):
				Pmax = 0
			else:
				Pmax = self.get_max_power()
				
			Pmin = 0.6 * Pmax
			
			t1 = self._tMax - offset
			t2 = self._tMax
			
			if temp < t1:
				P = Pmax
			elif temp > t2:
				P = Pmin
			else:
				Pmin = Pmax*0.6
				P = Pmax + (Pmin - Pmax) * (temp - t1)/(t2 - t1)
		else:
			P = 0
		
		if self._currentPower < P:
			self._currentPower += 0.05
		else:
			self._currentPower -= 0.5
			
	def getPower(self):
		return self._currentPower

	def get_max_flow_rate(self):
		return self._program.get_max_flow_rate()
	
	def getFlow(self):
		if self.getPumpState():
			return self.get_max_flow_rate() / 1000 # cube per hour
		return 0
		
	def getCoolDownPower(self):
		dt = self.get_temperature() - self._tMin
		return dt/self._tMax

	def getTotalPower(self):
		return self.getPower() - self.getCoolDownPower()

	def computeTemperature(self):
		flow = self.getFlow()
		direct_temp = self.get_temperature()
		if flow:
			temp = self.getSupplyBackwardTemperature()
		else:
			temp = direct_temp
			
		
		if flow:
			k = 0.9
			dt = self.getTotalPower() / flow * k
		else:
			dt = self.getTotalPower() * 0.5
		
		temp = limit(direct_temp - 1, temp + dt, direct_temp + 1) # don't want temp grow too fast
		
		temp = limit(self._tMin, temp, self._tMax + 10)

#		print(f'b{self._program.get_id()} t = {temp}')
		
		return temp

	def run(self):
		self.set_temperature(self.computeTemperature())
		self.computePower()


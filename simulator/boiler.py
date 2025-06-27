
import time
from functions.timeOnOffDelay import TimeOnOffDelay as TimeOnOffDelay

BROADCAST_ID = 0

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.getPreset()
		self._time_start    = time.time()
		self._control    = control
		
		self._boilerOverheatDelay = TimeOnOffDelay()
		
		self._inputId = {
			'temperature'         : 0,
			'backwardTemperature' : 1,
			'outsideRequest'      : 2,
			'error'               : 3,
		}

		self._outputId = {
			'pump'                : 0,
			'burner1'             : 1,
			'burner2'             : 2,
			'power'               : 3,
			'temperature'         : 4,
			'backwardTemperature' : 5,
		}

		self._tMax = 85
		self._tMin = 20
		self.setTemperature(30)

	def getSupplyBackwardTemperature(self):
		return self._control._collector.getSupplyBackwardTemperature()
	
	def getTemperature(self):
		return self._program.getInput(self._inputId['temperature']).getValue()

	def setTemperature(self, value):
#		print(f'boiler: {value}')
		self._program.getInput(self._inputId['temperature']).setValue(value)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getConsumersPower(self):
		consumersPower = self._control.getConsumersPower(self._program.getId())
		return consumersPower

	def temperatureInputIsMapped(self):
		temp = self._program.getInput(self._inputId['temperature'])
		mapping = temp.getMapping()
		if mapping is None:
			return False

		if mapping.getChannelType() == 'CHANNEL_UNDEFINED':
			return False

		return True


	def getStageState(self):
		stage = self._program.getOutput(self._outputId['burner1'])
		if stage.getMapping() is None:
			return 1

		if stage.getValue():
			return 1

		return 0
	
	def getPumpState(self):
		pumpState = self._program.getOutput(self._outputId['pump'])
		if pumpState.getMapping() is None:
			return 1

		if pumpState.getValue():
			return 1

		return 0
		

	def getMaxPower(self):
		return self._preset.getPower()

	def getPower(self):
		if self.getStageState():
			offset = 20
			temp = self.getTemperature()
			
			overheatOnDelay  = 30
			overheatOffDelay = 2*60
			
			if self._boilerOverheatDelay.Get(temp > self._tMax, overheatOnDelay, overheatOffDelay):
				return 0
			
			t1 = self._tMax - offset
			t2 = self._tMax
			
			Pmax = self.getMaxPower()
			Pmin = 0.6 * Pmax
			
			if temp < t1:
				P = Pmax
			elif temp > t2:
				P = Pmin
			else:
				Pmin = Pmax*0.6
				P = Pmax + (Pmin - Pmax) * (temp - t1)/(t2 - t1)
			
			return P
		else:
			return 0

	def getMaxFlowRate(self):
		return self._program.getMaxFlowRate()
	
	def getFlow(self):
		if self.getPumpState():
			return self.getMaxFlowRate() / 1000 # cube per hour
		return 0
		
	def getCoolDownPower(self):
		dt = self.getTemperature() - self._tMin
		return -1 * dt/self._tMax

	def getTotalPower(self):
		return self.getPower() + self.getConsumersPower() + self.getCoolDownPower()

	def computeTemperature(self):
		flow = self.getFlow()
		if flow:
			temp = self.getSupplyBackwardTemperature()
		else:
			temp = self.getTemperature()
			
		
		if flow:
			k = 0.7
			temp = temp + self.getTotalPower() / flow * k
		else:
			temp = temp + self.getTotalPower() * 0.5
		
		temp = limit(self._tMin, temp, self._tMax + 10)

#		print(f'b{self._program.getId()} t = {temp}')
		
		return temp

	def run(self):
		self.setTemperature(self.computeTemperature())




def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.getPreset()
		self._control    = control
		
		self.setTemperature(20)
		self.setBackwardTemperature(20)

	def getTemperature        (self): return self._program.getTemperature().getValue()
	def getBackwardTemperature(self): return self._backwardTemperature
	
	def setTemperature        (self, value): self._program.setTemperature(value)
	def setBackwardTemperature(self, value): self._backwardTemperature = value
		
	def getLoadingPumpState(self):
		pump = self._program.getLoadingPumpState()
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0
	
	def getCirculationPumpState(self):
		pump = self._program.getCirculationPumpState()
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0
	
	def getPumpState(self):
		if self.getCirculationPumpState() and self.getLoadingPumpState():
			return 1
		return 0

	def getMaxPower(self):
		return self._program.getMaxPower()
	

	def getPower(self):
		if self.getPumpState() == 0:
			return 0

		return self.getMaxPower()
	
	def getMaxFlowRate(self):
		return self._program.getMaxFlowRate()
	
	def getFlow(self):
		return self.getPumpState() * self.getMaxFlowRate() / 1000 # cube per hour
	
	def getSourceTemperature(self):
		return self._control._collector.getDirectTemperature()

	def getHeating(self):
		sourceTemp = self.getSourceTemperature()
		sourceTemp = sourceTemp - 5 # we loose some temp coming from source

		temp  = self.getTemperature()

		dT = sourceTemp - temp
		return dT * 0.003 * self.getPumpState()

	def getCooling(self):
		if self._washTime.Get(1*60, 10*60):
			return -0.1

		return -0.01 # should depend on shower time and so on

	def computeTemperature(self):
		temp  = self.getTemperature()

		temp = temp + self.getHeating() + self.getCooling()

		temp = limit(10, temp, 120)

		return temp
	
	def computeBackwardTemperature(self):
		if self.getPumpState() == 0:
			collectorBackwardTemp = self._control._collector.getBackwardTemperature()
			return collectorBackwardTemp
		
		temp = self.getTemperature()
		sourceTemp = self.getSourceTemperature()
		
		temp = (temp + sourceTemp)/2
		
		temp = limit(10, temp, 120)

		return temp

	def run(self):
		self.setTemperature        (self.computeTemperature())
		self.setBackwardTemperature(self.computeBackwardTemperature())

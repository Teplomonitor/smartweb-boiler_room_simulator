
from functions.periodPulse import PeriodPulse
from functions.limit import limit

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.get_preset()
		self._control    = control
		self._coldWaterTime = PeriodPulse()
		
		self.set_temperature(15)
		self.setBackwardTemperature(15)

	def get_temperature        (self): return self._program.get_temperature().get_value()
	def getBackwardTemperature(self): return self._backwardTemperature
	
	def set_temperature        (self, value): self._program.set_temperature(value)
	def setBackwardTemperature(self, value): self._backwardTemperature = value
		
	def getLoadingPumpState(self):
		pump = self._program.getLoadingPumpState()
		if pump.get_mapping() is None:
			return 1

		if pump.get_value():
			return 1

		return 0
	
	def getCirculationPumpState(self):
		pump = self._program.getCirculationPumpState()
		if pump.get_mapping() is None:
			return 1

		if pump.get_value():
			return 1

		return 0
	
	def getPumpState(self):
		if self.getCirculationPumpState() and self.getLoadingPumpState():
			return 1
		return 0

	def get_max_power(self):
		return self._program.get_max_power()
	

	def getPower(self):
		if self.getPumpState() == 0:
			return 0

		return self.get_max_power()
	
	def get_max_flow_rate(self):
		return self._program.get_max_flow_rate()
	
	def getFlow(self):
		return self.getPumpState() * self.get_max_flow_rate() / 1000 # cube per hour
	
	def getSourceTemperature(self):
		return self._control._collector.getDirectTemperature()

	def getHeating(self):
		sourceTemp = self.getSourceTemperature()
		sourceTemp = sourceTemp - 5 # we loose some temp coming from source

		temp  = self.get_temperature()

		dT = sourceTemp - temp
		return dT * 0.001 * self.getPumpState()

	def getCooling(self):
		if self._coldWaterTime.get(1*60, 10*60):
			return -0.1

		return -0.01 # should depend on shower time and so on

	def computeTemperature(self):
		temp  = self.get_temperature()

		temp = temp + self.getHeating() + self.getCooling()

		temp = limit(10, temp, 35)

		return temp
	
	def computeBackwardTemperature(self):
		if self.getPumpState() == 0:
			collectorBackwardTemp = self._control._collector.getBackwardTemperature()
			return collectorBackwardTemp
		
		temp = self.get_temperature()
		sourceTemp = self.getSourceTemperature()
		
		temp = (temp + sourceTemp)/2
		
		temp = limit(10, temp, 120)

		return temp

	def run(self):
		self.set_temperature        (self.computeTemperature())
		self.setBackwardTemperature(self.computeBackwardTemperature())


import time

from functions.periodPulse import PeriodPulse as PeriodPulse

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.getPreset()
		self._time_start    = time.time()
		self._control    = control
		self._washTime   = PeriodPulse()
		
		self._inputId = {
			'temperature'         : 0,
			'flow'                : 1,
			'backwardTemperature' : 2,
		}

		self._outputId = {
			'supplyPump'       : 0,
			'circPump'         : 1,
			'analogSupplyPump' : 2,
			'tptValveOpen'     : 3,
			'tptValveClose'    : 4,
		}

		self.setTemperature(20)


	def getTemperature(self):
		return self._program.getInput(self._inputId['temperature']).getValue()

	def setTemperature(self, value):
#		print(f'dhw: {value}')
		self._program.getInput(self._inputId['temperature']).setValue(value)

	def getBackwardTemperature(self):
		return self._program.getInput(self._inputId['backwardTemperature']).getValue()

	def setBackwardTemperature(self, value):
#		print(f'dhw: {value}')
		self._program.getInput(self._inputId['backwardTemperature']).setValue(value)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getPumpState(self):
		pump = self._program.getOutput(self._outputId['supplyPump'])
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0

	def getMaxPower(self):
		return self._preset.getPower()

	def getPower(self):
		if self.getPumpState() == 0:
			return 0

		return self.getMaxPower()

	def getFlow(self):
		return self.getPumpState() * 1 # cube per hour
	
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

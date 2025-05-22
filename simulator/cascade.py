
import math
import time


BROADCAST_ID = 0

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.getPreset()
		self._time_start    = time.time()
		self._control    = control
		
		self.setTemperature(30)

	def getTemperature(self):
		return self._program.getInput(0).getValue()

	def setTemperature(self, value):
#		print(f'cascade: {value}')
		self._program.getInput(0).setValue(value)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getConsumersPower(self):
		consumersPower = self._control.getConsumersPower(self._program.getId())
		return consumersPower

	def getPower(self):
		sourceList     = self._control.getSourceList()
		selfSourceList = self._program.getPreset().getSettings().getSourceList()

		power = 0
		for source in sourceList:
			if source._program.getId() in selfSourceList:
				power = power + source.getPower()

		return power

	def getCoolDownPower(self):
		return -1

	def getTotalPower(self):
		return self.getPower() + self.getConsumersPower() + self.getCoolDownPower()

	def computeTemperature(self):
		temp = self._control._collector.getDirectTemperature()
		
		temp = limit(-30, temp, 100)

		return temp

	def getFlow(self):
		return 0
		
#		sourceList     = self._control.getSourceList()
#		selfSourceList = self._program.getPreset().getSettings().getSourceList()

#		flow = 0
#		for source in sourceList:
#			if source._program.getId() in selfSourceList:
#				flow = flow + source.getFlow()

#		return flow
	
	def run(self):
		self.setTemperature(self.computeTemperature())

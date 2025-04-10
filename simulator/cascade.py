
import math
import time
from smartnet.units import TEMPERATURE as TEMPERATURE
from simulator.sensorReport import reportSensorValue as reportSensorValue


BROADCAST_ID = 0

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, thread_name, thread_ID, program, canbus, control):
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
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
		programList = self._control.getConsumerList()
		consumerList = []
		for program in programList:
			sourceList = program._program.getPreset().getSettings().getSourceList()
			if ((self._program.getId() in sourceList) or
				(BROADCAST_ID in sourceList) ):
				consumerList.append(program)

		consumerPower = 0
		for consumer in consumerList:
			consumerPower = consumerPower + consumer.getPower()

		return consumerPower

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
		temp = self.getTemperature()
		temp = temp + self.getTotalPower() * 0.05

		temp = limit(-30, temp, 120)

		return temp

	def run(self):
		self.setTemperature(self.computeTemperature())

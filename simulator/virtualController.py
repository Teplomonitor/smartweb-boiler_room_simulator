
import math
import time

VIRTUAL_SENSORS_MAX_NUM = 16

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._time_start = time.time()

		for i in range(0,VIRTUAL_SENSORS_MAX_NUM):
			self.setSensor(i, 20 + i*5)
	
	def getElapsedTime(self):
		return time.time() - self._time_start
	
	def getSensor(self, index):
		return self._program.getSensor(index).getValue()

	def setSensor(self, index, value):
#		print(f'oat: {value}')
		self._program.setSensor(index, value)

	def computeTemperature(self, index):
		value  = self.getSensor(index)

		pi = 3.14
		ds = math.cos(self.getElapsedTime()/100.0 + pi/2)

		value = value + ds * 0.1

		return value

	def run(self):
		for i in range(0,VIRTUAL_SENSORS_MAX_NUM):
			self.setSensor(i, self.computeTemperature(i))

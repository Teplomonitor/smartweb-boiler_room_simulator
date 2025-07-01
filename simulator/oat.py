
import math
import time


class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._time_start = time.time()

		self._inputId = {
			'temperature': 0,
		}

		self.setTemperature(-10)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getTemperature(self):
		return self._program.getInputChannel(self._inputId['temperature']).getValue()

	def setTemperature(self, value):
#		print(f'oat: {value}')
		self._program.getInputChannel(self._inputId['temperature']).setValue(value)

	def computeTemperature(self):
		temp  = self.getTemperature()

		pi = 3.14
		oat = math.cos(self.getElapsedTime()/1000.0 + pi/2)

		temp = temp + oat * 0.01

		return temp

	def run(self):
		self.setTemperature(self.computeTemperature())

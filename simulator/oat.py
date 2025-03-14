
import threading
import math
import time
from simulator.sensorReport import reportSensorValue as reportSensorValue

class Simulator(threading.Thread):
	def __init__(self, thread_name, thread_ID, program, canbus, control):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._program    = program
		self._time_start = time.time()

		self._inputId = {
			'temperature': 0,
		}

		self.setTemperature(-10)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getTemperature(self):
		return self._program.getInput(self._inputId['temperature']).getValue()

	def setTemperature(self, value):
		print(f'oat: {value}')
		self._program.getInput(self._inputId['temperature']).setValue(value)

	def computeTemperature(self):
		temp  = self.getTemperature()

		pi = 3.14
		oat = math.cos(self.getElapsedTime()/1000.0 + pi/2)

		temp = temp + oat

		return temp

	def run(self):
		while True:
			self.setTemperature(self.computeTemperature())
			time.sleep(5)

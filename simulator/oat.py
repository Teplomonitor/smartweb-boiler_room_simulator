
import math
import time


class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._time_start = time.time()

		self.set_temperature(-10)

	def get_elapsed_time(self):
		return time.time() - self._time_start
	
	def get_temperature(self):
		return self._program.getOutdoorTemperature().get_value()

	def set_temperature(self, value):
#		print(f'oat: {value}')
		self._program.getOutdoorTemperature().set_value(value)

	def compute_temperature(self):
		temp  = self.get_temperature()

		pi = 3.14
		oat = math.cos(self.get_elapsed_time()/1000.0 + pi/2)

		temp = temp + oat * 0.01

		return temp

	def run(self):
		self.set_temperature(self.compute_temperature())

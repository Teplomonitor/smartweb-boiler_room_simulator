
import math
import time


class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._time_start = time.time()

		self.setControlSignal(0)

	def getElapsedTime(self):
		return time.time() - self._time_start
	
	def getControlSignal(self):
		return self._program.getControlSignal().getValue()

	def setControlSignal(self, value):
#		print(f'oat: {value}')
		self._program.getControlSignal().setValue(value)

	def computeSignal(self):
		pi = 3.14
		t = self.getElapsedTime()
		Amp = 100.0
		A = Amp / 2
		offset = A
		signal = A * math.cos(2*pi*t/1000.0) * math.cos(2*pi*t/100.0) + offset

		return signal

	def run(self):
		self.setControlSignal(self.computeSignal())


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

	def getElapsedTime(self):
		return time.time() - self._time_start

	def computeOat(self):
		pi = 3.14
		oat = math.cos(self.getElapsedTime()/1000.0 + pi/2) * 20
		print(f'oat = {oat}')
		return oat

	def run(self):
		while True:
			self._program.getInput(0).setValue(self.computeOat())
			time.sleep(5)

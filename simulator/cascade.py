
import threading
import math
import time
from smartnet.units import TEMPERATURE as TEMPERATURE
from simulator.sensorReport import reportSensorValue as reportSensorValue

class Simulator(threading.Thread):
	def __init__(self, thread_name, thread_ID, program, canbus, control):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._program    = program
		self._preset     = self._program.getPreset()
		self._canbus        = canbus
		self._time_start    = time.time()
		
	def getElapsedTime(self):
		return time.time() - self._time_start


	def run(self):
		while True:
			time.sleep(2)


import threading
import math
import time
from smartnet.units import TEMPERATURE as TEMPERATURE
from simulator.sensorReport import reportSensorValue as reportSensorValue

class Simulator(threading.Thread):
	def __init__(self, thread_name, thread_ID, preset, canbus):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._preset     = preset
		self._canbus        = canbus
		self._time_start    = time.time()
		
		inputs = self._preset.getInputs()
		oatInput = inputs.getOat()
		self._sensorMapping = oatInput

	def getElapsedTime(self):
		return time.time() - self._time_start

	def reportOat(self, value):
		reportSensorValue(self._sensorMapping, value, self._canbus)

	def computeOat(self):
		pi = 3.14
		oat = math.cos(self.getElapsedTime()/1000.0 + pi/2) * 20
		print(f'oat = {oat}')
		return oat

	def run(self):
		while True:
			self.reportOat(TEMPERATURE(self.computeOat()))
			time.sleep(5)

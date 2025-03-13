
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
		self._time_start    = time.time()
		self._control    = control
		
		self.setTemperature(30)

	def getTemperature(self):
		return self._program.getInput(0).getValue()

	def setTemperature(self, value):
		self._program.getInput(0).setValue(value)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getConsumersPower(self):
		programList = self._control.getActiveProgramsList()
		consumerList = []
		for program in programList:
			pass

		return -5

	def getStageState(self):
		return 1

	def getPower(self):
		if self.getStageState():
			return self._preset.getPower()
		else:
			return 0

	def getTotalPower(self):
		return self.getPower() + self.getConsumersPower()

	def computeTemperature(self):
		temp = self.getTemperature()
		temp = temp + self.getTotalPower() * 0.1
		return temp

	def run(self):
		while True:
			self.setTemperature(self.computeTemperature())
			time.sleep(1)

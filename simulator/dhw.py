
import threading
import math
import time
from smartnet.units import TEMPERATURE as TEMPERATURE
from simulator.sensorReport import reportSensorValue as reportSensorValue

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(threading.Thread):
	def __init__(self, thread_name, thread_ID, program, canbus, control):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._program    = program
		self._preset     = self._program.getPreset()
		self._canbus        = canbus
		self._time_start    = time.time()
		self._control    = control
		
		self._inputId = {
			'temperature'         : 0,
			'flow'                : 1,
			'backwardTemperature' : 2,
		}

		self._outputId = {
			'supplyPump'       : 0,
			'circPump'         : 1,
			'analogSupplyPump' : 2,
			'tptValveOpen'     : 3,
			'tptValveClose'    : 4,
		}

		self.setTemperature(20)


	def getTemperature(self):
		return self._program.getInput(self._inputId['temperature']).getValue()

	def setTemperature(self, value):
		print(f'dhw: {value}')
		self._program.getInput(self._inputId['temperature']).setValue(value)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getPumpState(self):
		pump = self._program.getOutput(self._outputId['supplyPump'])
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0

	def getMaxPower(self):
		return self._preset.getPower()

	def getPower(self):
		if self.getPumpState() == 0:
			return 0

		return self.getMaxPower()

	def getSourceTemperature(self):
		sourceList = self._control.getSourceList()
		sourceId   = self._program.getPreset().getSettings().getSource()
		for source in sourceList:
			if source._program.getId() == sourceId:
				return source.getTemperature()

		return 60

	def getHeating(self):
		sourceTemp = self.getSourceTemperature()
		sourceTemp = sourceTemp - 5 # we loose some temp coming from source

		temp  = self.getTemperature()

		dT = sourceTemp - temp
		return dT * 0.01

	def getCooling(self):
		return -0.01 # should depend on shower time and so on

	def computeTemperature(self):
		temp  = self.getTemperature()

		temp = temp + self.getHeating() + self.getCooling()

		temp = limit(-30, temp, 120)

		return temp

	def run(self):
		while True:
			self.setTemperature(self.computeTemperature())
			time.sleep(2)

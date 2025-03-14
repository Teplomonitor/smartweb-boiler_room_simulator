
import math
import time

from smartnet.units import TEMPERATURE as TEMPERATURE
from simulator.sensorReport import reportSensorValue as reportSensorValue

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, thread_name, thread_ID, program, canbus, control):
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._program    = program
		self._preset     = self._program.getPreset()
		self._canbus        = canbus
		self._time_start    = time.time()
		self._control    = control
		
		self._outputId = {
			'analogValve'         : 0,
			'tptValveOpen'        : 1,
			'tptValveClose'       : 2,
			'pump'                : 3,
			'thermomotor'         : 4,
			'heatchangePump'      : 5,
			'analogPump'          : 6,
		}

		self._inputId = {
			'temperature'         : 0,
			'thermostat'          : 1,
			'outsideRequest'      : 2,
			'pumpControl'         : 3,
			'backwardTemperature' : 4,
		}

		self.setTemperature(20)

	def getOat(self):
		oat = self._control.getOat()
		if oat is None:
			oat = 0
			
		return oat.getTemperature()

	def getTemperature(self):
		return self._program.getInput(self._inputId['temperature']).getValue()

	def setTemperature(self, value):
		print(f'circuit: {value}')
		self._program.getInput(self._inputId['temperature']).setValue(value)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getPumpState(self):
		pump = self._program.getOutput(self._outputId['pump'])
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0

	def getValveState(self):
		valve = self._program.getOutput(self._outputId['analogValve'])
		if valve.getMapping() is None:
			return 1

		valve = valve.getValue()
		if valve is None:
			return 1
		return valve / 254

	def getMaxPower(self):
		return self._preset.getPower()

	def getPower(self):
		if self.getPumpState() == 0:
			return 0

		return self.getValveState()*self.getMaxPower()

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
		valve = self.getValveState()
		pump  = self.getPumpState()

		dT = sourceTemp - temp
		return dT * valve * pump 

	def getCooling(self):
		temp = self.getTemperature()
		oat  = self.getOat()
		dT = temp - oat

		return self.getMaxPower() * dT * 0.05 # should depend on weather and room temp

	def computeTemperature(self):
		temp  = self.getTemperature()

		temp = temp + self.getHeating() + self.getCooling()

		temp = limit(-30, temp, 120)

		return temp

	def run(self):
		self.setTemperature(self.computeTemperature())

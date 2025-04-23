
import math
import time


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
			'analogValve'     : 0,
			'tptValveOpen'    : 1,
			'tptValveClose'   : 2,
			'pump'            : 3,
			'thermomotor'     : 4,
			'heatchangePump'  : 5,
			'analogPump'      : 6,
		}

		self._inputId = {
			'temperature'         : 0,
			'thermostat'          : 1,
			'outsideRequest'      : 2,
			'pumpControl'         : 3,
			'backwardTemperature' : 4,
		}

		self._roomTemp = 24
		self.setTemperature(20)
		self.setBackwardTemperature(20)

	def getOat(self):
		oat = self._control.getOat()
		if oat is None:
			oat = 0
			
		return oat.getTemperature()
	
	def getRoomTemp(self):
		return self._roomTemp

	def getTemperature(self):
		return self._program.getInput(self._inputId['temperature']).getValue()

	def setTemperature(self, value):
		self._program.getInput(self._inputId['temperature']).setValue(value)

	def getBackwardTemperature(self):
		return self._program.getInput(self._inputId['backwardTemperature']).getValue()

	def setBackwardTemperature(self, value):
		self._program.getInput(self._inputId['backwardTemperature']).setValue(value)

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

	def computeTemperature(self):
		tempBackward = self.getBackwardTemperature()
		temp        = self.getTemperature()
		roomTemp    = self.getRoomTemp()

		if self.getPumpState() == 0:
			alpha = 0.01
			beta  = 1 - alpha
			return temp*beta + roomTemp*alpha

		sourceTemp = self.getSourceTemperature()
		sourceTemp = sourceTemp - 5 # we loose some temp coming from source

		valve = self.getValveState()
		
		temp = tempBackward + (sourceTemp - tempBackward) * valve

		temp = limit(-30, temp, 120)

		return temp
	
	def computeBackwardTemperature(self):
		temp       = self.getBackwardTemperature()
		roomTemp   = self.getRoomTemp()
		oat        = self.getOat()
		
		avrRoomTemp = (roomTemp*1.5 + oat*0.5)/2
		
		if self.getPumpState() == 0:
			alpha = 0.01
			beta  = 1 - alpha
			return temp*beta + avrRoomTemp*alpha
		
		tempDirect = self.getTemperature()
		
		alpha = 0.1
		beta  = 1 - alpha
		
		temp = tempDirect*beta + avrRoomTemp*alpha
		temp = limit(-30, temp, 120)

		return temp

	def run(self):
		self.setTemperature        (self.computeTemperature())
		self.setBackwardTemperature(self.computeBackwardTemperature())

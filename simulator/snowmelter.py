
import math
import time
from smartnet.units import TEMPERATURE as TEMPERATURE
from simulator.sensorReport import reportSensorValue as reportSensorValue
from functions.periodPulse import PeriodPulse as PeriodPulse

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, thread_name, thread_ID, program, canbus, control):
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._program    = program
		self._preset     = self._program.getPreset()
		self._canbus     = canbus
		self._time_start = time.time()
		self._control    = control
		self._snowTime   = PeriodPulse()
		
		self._inputId = {
			'directFlowTemperature'  : 0,
			'backwardTemperature'    : 1,
			'plateTemperature'       : 2,
			'snowSensor'             : 3,
		}

		self._outputId = {
			'primaryPump'              : 0,
			'secondaryPump'            : 1,
			'primaryPumpAnalogSignal'  : 2,
		}

		self.setDirectFlowTemperature  (20)
		self.setBackwardFlowTemperature(20)
		self.setPlateTemperature       ( 5)
		self.setSnowSensor             ( 0)
		
	def getOat(self):
		oat = self._control.getOat()
		if oat is None:
			oat = 0
			
		return oat.getTemperature()


	def getDirectFlowTemperature(self):
		return self._program.getInput(self._inputId['directFlowTemperature']).getValue()

	def setDirectFlowTemperature(self, value):
#		print(f'sm: direct flow temp = {value}')
		self._program.getInput(self._inputId['directFlowTemperature']).setValue(value)

	def getBackwardFlowTemperature(self):
		return self._program.getInput(self._inputId['backwardTemperature']).getValue()

	def setBackwardFlowTemperature(self, value):
#		print(f'sm: back flow temp = {value}')
		self._program.getInput(self._inputId['backwardTemperature']).setValue(value)

	def getPlateTemperature(self):
		return self._program.getInput(self._inputId['plateTemperature']).getValue()

	def setPlateTemperature(self, value):
#		print(f'sm: plate temp = {value}')
		self._program.getInput(self._inputId['plateTemperature']).setValue(value)

	def getSnowSensor(self):
		return self._program.getInput(self._inputId['snowSensor']).getValue()

	def setSnowSensor(self, value):
		self._program.getInput(self._inputId['snowSensor']).setValue(value)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getPrimaryPumpState(self):
		pump = self._program.getOutput(self._outputId['primaryPump'])
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0

	def getSecondaryPumpState(self):
		pump = self._program.getOutput(self._outputId['secondaryPump'])
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0
	
	def getAnalogPumpSignal(self):
		pump = self._program.getOutput(self._outputId['primaryPumpAnalogSignal'])
		if pump.getMapping() is None:
			return self.getPrimaryPumpState()

		value = pump.getValue()
		if value is None:
			return 0
		
		return value / 254

	def getMaxPower(self):
		return self._preset.getPower()

	def getPower(self):
		if self.getSecondaryPumpState() == 0:
			return 0

		return self.getMaxPower()*self.getAnalogPumpSignal()

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
		
#		print(f'sm: source temp = {sourceTemp}')
		temp       = self.getDirectFlowTemperature()
		backTemp   = self.getBackwardFlowTemperature()
		
		signal = self.getAnalogPumpSignal()
		pump   = self.getSecondaryPumpState()
		
		if pump:
			dT = sourceTemp - backTemp
			temp = backTemp + dT * signal
		
		return temp

	def getCooling(self):
		sourceTemp = self.getSourceTemperature()
		sourceTemp = sourceTemp - 5 # we loose some temp coming from source
		
		temp       = self.getDirectFlowTemperature()
		backTemp   = self.getBackwardFlowTemperature()
		plateTemp  = self.getPlateTemperature()
		
		signal = self.getAnalogPumpSignal()
		pump   = self.getSecondaryPumpState()
		
		if pump:
			dT = (temp - plateTemp)*0.8
			backTemp = plateTemp + dT * signal
		else:
			dT = sourceTemp - backTemp
			backTemp = backTemp + dT * signal
			
		return backTemp

	def getPlateHeating(self):
		temp       = self.getDirectFlowTemperature()
		backTemp   = self.getBackwardFlowTemperature()
		plateTemp  = self.getPlateTemperature()
		oat        = self.getOat()
		
		alpha = 0.3
		beta  = 1 - alpha
		
		plateTemp = plateTemp * beta + oat * alpha
		
		signal = self.getAnalogPumpSignal()
		pump   = self.getSecondaryPumpState()

		if pump:
			tempAver = (temp + backTemp)/2
			dT = (tempAver - plateTemp) * 0.5
			plateTemp = plateTemp + dT * signal
		
		return plateTemp

	def computeDirectFlowTemperature(self):
		temp       = self.getDirectFlowTemperature()

		alpha = 0.3
		beta  = 1 - alpha

		temp = temp * beta + self.getHeating() * alpha
		
		temp = limit(-30, temp, 120)

		return temp

	def computeBackwardFlowTemperature(self):
		temp   = self.getBackwardFlowTemperature()

		alpha = 0.1
		beta  = 1 - alpha

		temp = temp * beta + self.getCooling() * alpha
		
		temp = limit(-30, temp, 120)

		return temp

	def computePlateTemperature(self):
		temp = self.getPlateTemperature()

		alpha = 0.001
		beta  = 1 - alpha

		temp = temp * beta + self.getPlateHeating() * alpha
		
		temp = limit(-30, temp, 120)

		return temp

	def run(self):
		self.setDirectFlowTemperature  (self.computeDirectFlowTemperature())
		self.setBackwardFlowTemperature(self.computeBackwardFlowTemperature())
		self.setPlateTemperature       (self.computePlateTemperature())

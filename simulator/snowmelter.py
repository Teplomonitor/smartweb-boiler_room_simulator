
import math
import time

from functions.periodPulse import PeriodPulse as PeriodPulse

S = 5*4
h = 0.15
p = 2200

V = S*h
M = V*p

concreteHeatCapacity = 880

CHCM = concreteHeatCapacity * M

heatTransferCoefficient = 10
A = 15


def computeNHeating(Tplate, Tavr):
	return heatTransferCoefficient*S*(Tavr-Tplate)

def computeNCooling(Tplate, Toat):
	return A*S*(Toat - Tplate)

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
		self._cnt        = 0

		
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
		self.setPlateTemperature       (-5)
		self.setSnowSensor             ( 0)
		
	def getOat(self):
#		return -10
		oat = self._control.getOat()
		if oat is None:
			oat = 0
			
		return oat.getTemperature()


	def getDirectFlowTemperature(self):
#		return 50
		return self._program.getInput(self._inputId['directFlowTemperature']).getValue()

	def setDirectFlowTemperature(self, value):
#		print(f'sm: direct flow temp = {value}')
		self._program.getInput(self._inputId['directFlowTemperature']).setValue(value)

	def getBackwardFlowTemperature(self):
#		return 30
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
			if signal:
				dT = sourceTemp - backTemp
				temp = backTemp + dT * signal
			else:
				plateTemp = self.getPlateTemperature()
				temp = (temp + plateTemp)/2
		
		return temp

	def getCooling(self):
		temp       = self.getDirectFlowTemperature()
		backTemp   = self.getBackwardFlowTemperature()
		plateTemp  = self.getPlateTemperature()
		
		signal = self.getAnalogPumpSignal()
		pump   = self.getSecondaryPumpState()
		
		if pump:
			dT = temp - plateTemp
			backTemp = plateTemp + dT * signal
		else:
			sourceTemp = self.getSourceTemperature()
			sourceTemp = sourceTemp - 5 # we loose some temp coming from source
			dT = sourceTemp - backTemp
			backTemp = backTemp + dT * signal
			
		return backTemp

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
		temp       = self.getPlateTemperature()
		directTemp = self.getDirectFlowTemperature()
		backTemp   = self.getBackwardFlowTemperature()
		oat        = self.getOat()
		pump       = self.getSecondaryPumpState()

		if pump:
			Tavr = (directTemp + backTemp)/2
			nHeating = computeNHeating(temp, Tavr)
		else:
			nHeating = 0
			
		nCooling = computeNCooling(temp, oat)
		n = nHeating + nCooling
		
		temp = temp + n / CHCM
		
		temp = limit(oat, temp, 80)

		return temp

	def run(self):
		self.setDirectFlowTemperature  (self.computeDirectFlowTemperature())
		self.setBackwardFlowTemperature(self.computeBackwardFlowTemperature())
		self.setPlateTemperature       (self.computePlateTemperature())

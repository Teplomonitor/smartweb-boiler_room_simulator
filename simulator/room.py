
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
		self._canbus        = canbus
		self._time_start    = time.time()
		self._control    = control
		self._washTime   = PeriodPulse()
		
		self._inputId = {
			'roomTemperature'   : 0,
			'mode_deprecated'   : 1,
			'floorTemperature'  : 2,
			'wallTemperature'   : 3,
			'humidity'          : 4,
			'CO2'               : 5,
			'motion'            : 6,
		}

		self._outputId = {
			'valve1'       : 0,
			'valve2'       : 1,
			'valve3'       : 2,
			'analogValve1' : 3,
			'analogValve2' : 4,
			'analogValve3' : 5,
		}

		self.setTemperature(20)


	def getOat(self):
		oat = self._control.getOat()
		if oat is None:
			oat = 0
			
		return oat.getTemperature()

	def getTemperature(self):
		return self._program.getInput(self._inputId['roomTemperature']).getValue()

	def setTemperature(self, value):
		self._program.getInput(self._inputId['roomTemperature']).setValue(value)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getMaxPower(self):
		return self._preset.getPower()

	def getPower(self):
		if self.getPumpState() == 0:
			return 0

		return self.getMaxPower()

	def getSourceTemperature(self, sourceId):
		sourceList       = self._control.getHeatingCircuitList()
		roomSourceList   = self._program.getPreset().getSettings().getSourceList()
#		print(f'source list {roomSourceList}')
		for source in sourceList:
			programId = source._program.getId()
#			print(f'source id = {programId}')
			if programId == roomSourceList[sourceId]:
#				print(f'source {sourceId} found')
				if source.getPower():
					return source.getTemperature()

		return self.getTemperature()
	
	def getSourcePower(self, sourceId):
		sourceList       = self._control.getHeatingCircuitList()
		roomSourceList   = self._program.getPreset().getSettings().getSourceList()
		for source in sourceList:
			if source._program.getId() == roomSourceList[sourceId]:
				return source.getPower()

		return 0
	
	def getFloorPower(self):
		return self.getSourcePower(0)
	
	def getRadiatorPower(self):
		return self.getSourcePower(1)
	
	def getAdditionalSourcePower(self):
		return self.getSourcePower(2)

	def getFloorTemperature(self):
		return self.getSourceTemperature(0)
	
	def getRadiatorTemperature(self):
		return self.getSourceTemperature(1)
	
	def getAdditionalSourceTemperature(self):
		return self.getSourceTemperature(2)

	def getHeating(self):
		floorTemp    = self.getFloorTemperature()
		radiatorTemp = self.getRadiatorTemperature()
		wallTemp     = self.getAdditionalSourceTemperature()
		
		
		temp  = self.getTemperature()
		
#		print(f'floor={floorTemp} rad={radiatorTemp} wall={wallTemp} self={temp}')
		
		dTrad   = radiatorTemp - temp
		dTfloor = floorTemp    - temp
		dTwall  = wallTemp     - temp
		
		return dTfloor*0.0015 + dTrad*0.001 + dTwall*0.001

	def getCooling(self):
		temp  = self.getTemperature()
		oat   = self.getOat()
		
		dT = oat - temp
		
		return dT*0.001
		

	def computeTemperature(self):
		temp  = self.getTemperature()

		temp = temp + self.getHeating() + self.getCooling()

		temp = limit(-10, temp, 50)

		return temp

	def run(self):
		self.setTemperature(self.computeTemperature())

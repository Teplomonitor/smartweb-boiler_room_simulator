'''
@author: admin
'''

import time

from consoleLog import printLog   as printLog
from consoleLog import printError as printError
from scenario.scenario import Scenario   as Parent

from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._snowmelter = self._programList['snowmelter']
		self._outdoor    = self._programList['oat']

	def getScenarioTitle(self): return 'scenario 1'
	
	def getScenarioDescription(self):
		return 'check if circulation pump switch off, if T < TfrostProtect'
	
	def getChecklistId(self): return '3.9.1'
	
	def getRequiredPrograms(self):
		requiredProgramTypesList = {
			'snowmelter': 'SNOWMELT',
			'oat'       : 'OUTDOOR_SENSOR',
		}
		return requiredProgramTypesList
	
	def getDefaultPreset(self): return 'snowmelter'

	def readFrostProtectionTemperatureValue(self): return self._snowmelter.readParameterValue('frostProtectionTemp')
	def readRequiredPlateTemperatureValue(self)  : return self._snowmelter.readParameterValue('reqPlateTemp')
	def readMinOutdoorTemperature(self)          : return self._snowmelter.readParameterValue('minOutdoorTemp')
	def readMaxOutdoorTemperature(self)          : return self._snowmelter.readParameterValue('maxOutdoorTemp')
		
	def setPlateTemperature(self, value):
		t = self._snowmelter.getPlateTemperature()
		self.setSensorValue(t, value)
		
	def setOutdoorTemperature(self, value):
		t = self._outdoor.getOutdoorTemperature()
		self.setSensorValue(t, value)
		
	def setMediumOutdoorTemperature(self):
		minTemp = self.readMinOutdoorTemperature()
		maxTemp = self.readMaxOutdoorTemperature()
		
		midTemp = (minTemp + maxTemp)/2
		self.setOutdoorTemperature(midTemp)

	def getCirculationPumpState(self):
		return self._snowmelter.getSecondaryPumpState().getValue()
	
	def setBacwardFlowTemperature(self, value):
		t = self._snowmelter.getBackwardFlowTemperature()
		self.setSensorValue(t, value)
		
	def waitPumpSwitchOn(self, delay):
		pumpNotWorkingDelay = TimeOnDelay()
		
		pump = False
		
		while not pump:
			time.sleep(1)
			
			pump = self.getCirculationPumpState()
			if pumpNotWorkingDelay.Get(not pump, delay):
				return False
			
		return True
	
	def waitPumpSwitchOff(self, delay, timeout):
		pumpNotWorkingDelay = TimeOnDelay()
		testTimeoutDelay    = TimeOnDelay()
		
		while True:
			time.sleep(1)
			
			pump = self.getCirculationPumpState()
			if pumpNotWorkingDelay.Get(not pump, delay):
				return True
			
			if testTimeoutDelay.Get(True, timeout):
				return False
		return False
	
	def run(self):
		plateSetpoint = self.readRequiredPlateTemperatureValue()
		
		if plateSetpoint is None:
			self._status = 'FAIL'
			printError('Проблема! не удалось получить уставку плиты')
			return
		
		tFrostProtect = self.readFrostProtectionTemperatureValue()
		
		if tFrostProtect is None:
			self._status = 'FAIL'
			printError('Test fail! Can\'t get frost protect temp')
			return
		
		printLog('делаем подходящую для снеготайки уличную температуру')
		self.setMediumOutdoorTemperature()
		time.sleep(3)
		
		printLog('делаем плиту холодной')
		self.setPlateTemperature(plateSetpoint - 2)
		time.sleep(3)
		
		printLog('Warm up')
		time.sleep(30)
		
		printLog('Waiting for circulation pump to switch on')
		if self.waitPumpSwitchOn(60):
			printLog('ok, cirulation pump is working')
		else:
			self._status = 'FAIL'
			printError('Test fail! Pump don\'t work')
			return
			
		time.sleep(2)
		
		printLog('making "cold" backward flow temperature')
		self.setBacwardFlowTemperature(tFrostProtect - 1)
		
		pumpSwitchOffDuration = 60
		
		printLog(f'Waiting for circulation pump to switch off for at least {pumpSwitchOffDuration} seconds')
		time.sleep(10)
		
		if self.waitPumpSwitchOff(pumpSwitchOffDuration, 5*60):
			printLog('Test Ok!')
			self._status = 'OK'
		else:
			printError('Test fail! Pump don\'t switch off')
			self._status = 'FAIL'
		


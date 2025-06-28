'''
@author: admin
'''

import time

from scenario.scenario import printLog   as printLog
from scenario.scenario import printError as printError
from scenario.scenario import Scenario   as Parent

from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self.initScenario()
		
		self._snowmelter = self._programList['snowmelter']

	def getScenarioTitle(self):
		return 'scenario 1'
	
	def getScenarioDescription(self):
		return 'check if circulation pump switch off, if T < TfrostProtect'
	
	def getRequiredPrograms(self):
		requiredProgramTypesList = {
			'snowmelter': 'SNOWMELT',
			'oat'       : 'OUTDOOR_SENSOR',
		}
		return requiredProgramTypesList
	
	def getDefaultPreset(self):
		return 'snowmelter'
		
		
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
		
		pump = False
		
		while True:
			time.sleep(1)
			
			pump = self.getCirculationPumpState()
			if pumpNotWorkingDelay.Get(not pump, delay):
				return True
			
			if testTimeoutDelay(True, timeout):
				return False
		return False
	
	def run(self):
		printLog('Warm up')
		time.sleep(30)
		
		if self.waitPumpSwitchOn(60):
			printLog('ok, cirulation pump is working')
		else:
			self._status = 'FAIL'
			printError('Test fail! Pump don\'t work')
			return
			
		time.sleep(2)
		
		printLog('making "cold" backward flow temperature')
		self.setBacwardFlowTemperature(0)
		
		time.sleep(10)
		
		if self.waitPumpSwitchOff(60, 5*60):
			printLog('Test Ok!')
			self._status = 'OK'
		else:
			printLog('Test fail!')	
			self._status = 'FAIL'
		


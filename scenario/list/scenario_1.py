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
		
	def setBacwardFlowTemperature(self, value):
		t = self._snowmelter.getBackwardFlowTemperature()
		self.setSensorValue(t, value)
		
		
	def run(self):
		pumpNotWorkingDelay = TimeOnDelay()
		testTimeoutDelay    = TimeOnDelay()
		
		printLog('Warm up')
		time.sleep(30)
		
		
		
		while True:
			time.sleep(1)
			
			pump = self._snowmelter.getSecondaryPumpState().getValue()
			if pumpNotWorkingDelay.Get(not pump, 60):
				self._done = True
				printError('Test fail! Pump don\'t work')
				return
			
			if pump:
				printLog('cirulation pump is working')
				break
			
			
		time.sleep(2)
		
		printLog('making "cold" backward flow temperature')
		self.setBacwardFlowTemperature(0)
		
		time.sleep(10)
		
		while True:
			time.sleep(1)
			
			pump = self._snowmelter.getSecondaryPumpState().getValue()
			
			if pumpNotWorkingDelay.Get(not pump, 60):
				self._done = True
				printLog('Test Ok!')
				return
			
			if testTimeoutDelay.Get(True, 5*60):
				self._done = True
				printLog('Test fail!')
				return
				
			
	
	def done(self):
		return self._done


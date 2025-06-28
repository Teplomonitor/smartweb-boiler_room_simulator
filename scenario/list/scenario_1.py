'''
@author: admin
'''

import presets.preset
import time
from scenario.scenario import printLog   as printLog
from scenario.scenario import printError as printError
from scenario.scenario import Scenario as Parent

# check if circulation pump switch off, if T < TfrostProtect

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		printLog('starting scenario 1')
		
		self.initScenario()
		
		self._snowmelter = self._programList['snowmelter']

	def getRequiredPrograms(self):
		requiredProgramTypesList = {
			'snowmelter': 'SNOWMELT',
			'oat'       : 'OUTDOOR_SENSOR',
		}
		return requiredProgramTypesList
	
	def getDefaultPreset(self):
		return 'snowmelter'
		
	def run(self):
		if self.done():
			return
		
		time.sleep(20)
		
		timeStart = time.time()
		
		while True:
			pump = self._snowmelter.getSecondaryPumpState().getValue()
			if pump:
				break
			
			if time.time() - timeStart > 5*60:
				self._done = True
				printLog('Test fail! Pump don\'t work')
				return
			time.sleep(1)
			
		t = self._snowmelter.getBackwardFlowTemperature()
		
		self.setSensorValue(t, 0)
		
		time.sleep(10)
		
		timeStart = time.time()
		
		while True:
			pump = self._snowmelter.getSecondaryPumpState().getValue()
			
			if not pump:
				self._done = True
				printLog('Test Ok!')
				return
			
			if time.time() - timeStart > 5*60:
				self._done = True
				printLog('Test fail!')
				return
				
			
			time.sleep(1)
	
	def done(self):
		return self._done


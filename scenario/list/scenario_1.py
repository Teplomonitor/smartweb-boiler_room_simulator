'''
@author: admin
'''

import presets.preset
from scenario.scenario import printLog   as printLog
from scenario.scenario import printError as printError
from scenario.scenario import Scenario as Parent

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		printLog('starting scenario 1')
		
		self.initScenario()

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
		printLog('running scenario 1')
	
	def done(self):
		return self._done


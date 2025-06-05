'''
@author: admin
'''

import presets.preset
from scenario.scenario import printLog   as printLog
from scenario.scenario import printError as printError
from controllers.controller_io import initVirtualControllers as initVirtualControllers

class Scenario():
	def __init__(self, controllerHost, sim):
		printLog('starting scenario 1')
		self._default_preset = 'snowmelter'
		self._controllerHost = controllerHost
		self._done = False
		self._snowmelterProgram = self.getProgramByType('SNOWMELT')
		self._sim = sim
		
		if self._snowmelterProgram is None:
			self._done = True
			printError('Snowmelter not in program list!')
			programList, controllerIoList = presets.preset.getPresetsList(self._default_preset)
			self._controllerHost.initController(True, programList)
			ctrlIo = initVirtualControllers(controllerIoList)
			self._sim.resetControllerConfig(self._controllerHost, ctrlIo)
			
			self._snowmelterProgram = self.getProgramByType('SNOWMELT')
			if self._snowmelterProgram is None:
				printError('WTF?!')
			else:
				printLog('Snowmelter found!')
				
		else:
			printLog('Snowmelter found!')
			
		
	
	def getProgramList(self):
		return self._controllerHost.getProgramList()
	
	def getProgramByType(self, programType):
		programsList = self.getProgramList()
		for program in programsList:
			if program.getType() == programType:
				return program
		
		return None
		
	def run(self):
		if self.done():
			return
		pass
	
	def done(self):
		return self._done


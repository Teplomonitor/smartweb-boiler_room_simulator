'''
@author: admin
'''
from os.path import dirname, basename, isfile, join
import glob

import time
import threading

import presets.preset
from controllers.controller_io import initVirtualControllers as initVirtualControllers

from gui.frame import printLog   as printLog
from gui.frame import printError as printError


class Scenario(object):
	def __init__(self, controllerHost, sim):
		self._controllerHost = controllerHost
		self._status = 'IN_PROGRESS'
		self._sim = sim
				
		printLog(f'starting {self.getScenarioTitle()}')
		printLog(f'description: {self.getScenarioDescription()}')
		
		self._manualSensorsList = []
	
	def getScenarioTitle(self):
		return 'scenario'
	
	def getScenarioDescription(self):
		return 'default'
	
	def __del__(self):
		for sensor in self._manualSensorsList:
			sensor.setManual(False)
			
	def setManual(self, sensor, manual):
		sensor.setManual(manual)
		if sensor in self._manualSensorsList:
			return
		self._manualSensorsList.append(sensor)
	
	def setSensorValue(self, sensor, value):
		self.setManual(sensor, True)
		sensor.setValue(value, True)
		
	def done(self):
		return self._status is not 'IN_PROGRESS'
	
	def initScenario(self):
		ok = self.initProgramList(self.getRequiredPrograms())
				
		if not ok:
			self.initController(self.getDefaultPreset())
			
			if not self.initProgramList(self.getRequiredPrograms()):
				printError('WTF?!')
			else:
				printLog('init ok!')

	def getRequiredPrograms(self):
		requiredProgramTypesList = {
		}
		return requiredProgramTypesList
		
	def getDefaultPreset(self):
		return 'default'
	
	def initController(self, preset):
		programList, controllerIoList = presets.preset.getPresetsList(preset)
		self._controllerHost.initController(True, programList)
		ctrlIo = initVirtualControllers(controllerIoList)
		self._sim.reloadConfig(self._controllerHost, ctrlIo)
		
	def initProgramList(self, requiredProgramTypesList):
		self._programList = {}
		for prgKey in requiredProgramTypesList:
			prg = self.getUnbindedProgram(requiredProgramTypesList[prgKey])
			if prg is None:
				printError(f'{prgKey} not in program list!')
				return False
			else:
				self._programList[prgKey] = prg
		return True
		
	def getProgramList(self):
		return self._controllerHost.getProgramList()
	
	def findProgramInList(self, program):
		return [_ for _, prg in self._programList.items() if prg == program]
	
	def getUnbindedProgram(self, programType):
		programsList = self.getProgramList()
		for program in programsList:
			if program.getType() == programType:
				# in case we need to different programs of the same type
				if self.findProgramInList(program):
					#this one already in list
					continue
				else:
					return program
		return None

class ScenarioThread(threading.Thread):
	'''
	classdocs
	'''
	def __init__(self, controllerHost, simulator):
		'''
		Constructor
		'''
		threading.Thread.__init__(self)
		
		self._scenarioIndex = 0
		self._controllerHost = controllerHost
		self._simulator      = simulator
		self._programsList   = self._controllerHost.getProgramList()
		
		self._currentScenario = self.getNextScenario()
		
	def getNextScenario(self):
		scenario = self.getScenario(self._scenarioIndex)
		self._scenarioIndex = self._scenarioIndex + 1
		return scenario
		
	def run(self):
		while True:
			self._currentScenario.run()
			
			if self._currentScenario.done():
				self._currentScenario = self.getNextScenario()
				if self._currentScenario == None:
					printLog('All scenario finished!')
					return 0
				
			time.sleep(1)

	def getScenario(self, scenarioIndex):
		regex = join(dirname(__file__),'list', "*.py")
		
		modules = glob.glob(regex)
		__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
		
		if scenarioIndex < len(__all__): 
			scenarioId = __all__[scenarioIndex]
			moduleId = 'scenario.list.%s' % scenarioId
			scenario_module = __import__(moduleId, fromlist=["scenario.list"])
			return scenario_module.Scenario(self._controllerHost, self._simulator)
		
		return None


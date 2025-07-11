'''
@author: admin
'''
from os.path import dirname, basename, isfile, join
import glob

import time
import threading

import main
import mainThread

from consoleLog import printLog   as printLog
from consoleLog import printError as printError


class Scenario(object):
	def __init__(self, controllerHost, sim):
		self._controllerHost = controllerHost
		self._status = 'IN_PROGRESS'
		self._sim = sim
				
		printLog(f'starting {self.getScenarioTitle()}')
		printLog(f'description: {self.getScenarioDescription()}')
		
		self._manualSensorsList = []
	
		self.initScenario()
		
	def getScenarioTitle(self):
		return 'scenario'
	
	def getScenarioDescription(self):
		return 'default'
	
	def getChecklistId(self):
		return '--'
	
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
		return self._status != 'IN_PROGRESS'
	
	def getStatus(self):
		return self._status
	
	def initScenario(self):
		ok = self.initProgramList(self.getRequiredPrograms())
				
		if not ok:
			main.loadPreset(self.getDefaultPreset())
			
			while main.loadPresetDone() == False:
				time.sleep(1)
			
			time.sleep(2)
			
			if not self.initProgramList(self.getRequiredPrograms()):
				printError('fail to init program list!')
			else:
				printLog('init ok!')

	def getRequiredPrograms(self):
		requiredProgramTypesList = {
		}
		return requiredProgramTypesList
		
	def getDefaultPreset(self):
		return 'default'
	
	def initProgramList(self, requiredProgramTypesList):
		self._programList = {}
		for prgKey in requiredProgramTypesList:
			prg = self.getUnbindedProgram(requiredProgramTypesList[prgKey])
			if prg is None:
				printError(f'{prgKey} not in program list!')
				self._programList = {}
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

def getScenarioFilesList():
	regex = join(dirname(__file__),'list', "*.py")
	
	modules = glob.glob(regex)
	__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
	return __all__

class ScenarioThread(threading.Thread):
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, 'instance'):
			cls.instance = super(threading.Thread, cls).__new__(cls)
		return cls.instance

	def __init__(self, controllerHost = None, simulator = None):
		if hasattr(self, '_initDone'):
			return
		
		threading.Thread.__init__(self, name = 'Scenario')
		
		self._scenarioIndex = 0
		self._currentScenario = None
		self._controllerHost = controllerHost
		self._simulator      = simulator
		self._newScenario    = None
		self._scenarioResultList = []
		
		self._initDone = True
		
		self.daemon = True
		self.start()
		
	def getNextScenario(self):
		scenario = self.getScenario(self._scenarioIndex)
		self._scenarioIndex += 1
		return scenario
		
	def run(self):
		while mainThread.taskEnable():
			if self._newScenario:
				self.startScenarioNow(self._newScenario)
				self._newScenario = None
			
			if self._currentScenario:
				self._currentScenario.run()
			
				if self._currentScenario.done():
					self.appendScenarioResult(self._currentScenario)
					
					self._currentScenario = self.getNextScenario()
					if self._currentScenario == None:
						self.printScenarioRunResult()
				
			time.sleep(1)
			
	def appendScenarioResult(self, scenario):
		result = {
			'checklistId': scenario.getChecklistId(),
			'result'     : scenario.getStatus()
		}
		self._scenarioResultList.append(result)
		
	def printScenarioRunResult(self):
		dt = time.time() - self._scenarioStartTime
		printLog('All scenario finished!')
		printLog(f'Time: {dt} seconds')
		
		for result in self._scenarioResultList:
			checklistId = result['checklistId']
			value = result['result']
			
			if value == 'OK':
				printFunc = printLog
			else:
				printFunc = printError
			
			printFunc(f'{checklistId}: {value}')
				
	def startScenario(self, scenario):
		self._newScenario = scenario
	
	def startScenarioNow(self, scenario):
		self._scenarioStartTime = time.time()
		self._scenarioResultList = []
		
		if scenario == 'all':
			self._scenarioIndex = 0
			self._currentScenario = self.getNextScenario()
			return
		
		__all__ = getScenarioFilesList()
		
		if scenario in __all__:
			self._scenarioIndex   = len(__all__)
			self._currentScenario = self.getScenarioModule(scenario)
		else:
			printError(f'{scenario} not in scenario list!')
			
	
	def getScenarioModule(self, scenarioId):
		moduleId = 'scenario.list.%s' % scenarioId
		scenario_module = __import__(moduleId, fromlist=["scenario.list"])
		return scenario_module.Scenario(self._controllerHost, self._simulator)

	def getScenario(self, scenarioIndex):
		__all__ = getScenarioFilesList()
		
		if scenarioIndex < len(__all__): 
			scenarioId = __all__[scenarioIndex]
			return self.getScenarioModule(scenarioId)
		
		return None

def startScenario(scenario):
	ScenarioThread().startScenario(scenario)

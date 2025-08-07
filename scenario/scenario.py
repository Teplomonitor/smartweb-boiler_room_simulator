'''
@author: admin
'''

import os
from os.path import dirname, join

from pydoc import importfile
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
		self._startTime = time.time()
		self._EventStop = ScenarioThread().getStopScenarioEvent()
				
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
	
	def getDuration(self):
		return time.time() - self._startTime
	
	def setManual(self, sensor, manual):
		sensor.setManual(manual)
		if sensor in self._manualSensorsList:
			return
		self._manualSensorsList.append(sensor)
		
	def is_stopped(self):
		return (mainThread.taskEnable() == False) or self._EventStop.is_set()
	
	def wait(self, delay):
		if self.is_stopped():
			return False
		
		if delay < 3:
			time.sleep(delay)
			return True
		
		i = 0
		while i < delay:
			if self.is_stopped():
				return False
		
			i += 1
			time.sleep(1)
		
		return True
	
	def setSensorValue(self, sensor, value):
		self.setManual(sensor, True)
		sensor.setValue(value, True)
		
	def done(self):
		return self._status != 'IN_PROGRESS'
	
	def clear(self):
		for prg in self._programList.values():
			prg.enableGuiControl()
			
		for sensor in self._manualSensorsList:
			sensor.setManual(False)
	
	def getStatus(self):
		return self._status
	
	def initScenario(self):
		ok = self.initProgramList(self.getRequiredPrograms())
				
		if not ok:
			main.loadPreset(self.getDefaultPreset())
			
			while main.loadPresetDone() == False:
				self.wait(1)
			
			self.wait(2)
			
			if not self.initProgramList(self.getRequiredPrograms()):
				printError('fail to init program list!')
			else:
				printLog('init ok!')
				ok = True
				
		if ok:
			for prg in self._programList.values():
				prg.disableGuiControl()
				
		self._startTime = time.time()

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

def getScenarioDir():
	return join(dirname(__file__),'list')

def getScenarioFilesList():
	__all__ = []
	
	def addScenarioItems(scenarioDir):
		def filterScenarioItems():
			if '__pycache__' in dirs : dirs .remove('__pycache__')  # don't visit __pycache__ directories
			if '__init__.py' in files: files.remove('__init__.py')  # don't use __init__.py files
			
		for root, dirs, files in os.walk(scenarioDir):
			filterScenarioItems()
			print(f'{root} -- {dirs} -- {files}')
			
			for scenarioFile in files:
				__all__.append(join(scenarioDir, scenarioFile))
				
			for scenarioSubDir in dirs:
				addScenarioItems(os.path.join(scenarioDir, scenarioSubDir))
				
			break
			
	
	addScenarioItems(getScenarioDir())
	
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
		self._stopScenarioEvent = threading.Event()
		self._scenarioList = getScenarioFilesList()
		self._initDone = True
		
		self.daemon = True
		self.start()
	
	def getStopScenarioEvent(self):
		return self._stopScenarioEvent
	
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
					self._currentScenario.clear()
					self._currentScenario = self.getNextScenario()
					if self._currentScenario == None:
						self.printScenarioRunResult()
							
			if self._stopScenarioEvent.is_set():
				self._stopScenarioEvent.clear()
				if self._currentScenario:
					printError(f'Сцераний прерван по внешнему запросу')
					self._currentScenario.clear()
					self._currentScenario = None
					self.printScenarioRunResult()
					
			time.sleep(1)
			
	def appendScenarioResult(self, scenario):
		result = {
			'checklistId': scenario.getChecklistId(),
			'result'     : scenario.getStatus(),
			'duration'   : scenario.getDuration()
		}
		self._scenarioResultList.append(result)
		
	def printScenarioRunResult(self):
		dt = time.time() - self._scenarioStartTime
		dtStr = time.strftime('%H:%M:%S', time.gmtime(dt))

		printLog('All scenario finished!')
		printLog(f'Time: {dtStr}')
		
		for result in self._scenarioResultList:
			checklistId = result['checklistId']
			value       = result['result']
			duration    = result['duration']
			durationStr = time.strftime('%H:%M:%S', time.gmtime(duration))
			if value == 'OK':
				printFunc = printLog
			else:
				printFunc = printError
			
			printFunc(f'{checklistId}: {value} ({durationStr})')
				
	def startScenario(self, scenario):
		self._newScenario = scenario
	
	def startScenarioNow(self, scenario):
		self._scenarioStartTime = time.time()
		self._scenarioResultList = []
		
		if scenario == 'all':
			self._scenarioIndex = 0
			self._currentScenario = self.getNextScenario()
			return
		
		__all__ = self._scenarioList
		
		if scenario in __all__:
			self._scenarioIndex   = len(__all__)
			self._currentScenario = self.getScenarioObject(scenario)
		else:
			printError(f'{scenario} not in scenario list!')
			
	
	def getScenarioObject(self, scenarioId):
		scenario_module = importfile(scenarioId)
		return scenario_module.Scenario(self._controllerHost, self._simulator)

	def getScenario(self, scenarioIndex):
		__all__ = self._scenarioList
		
		if scenarioIndex < len(__all__): 
			scenarioId = __all__[scenarioIndex]
			return self.getScenarioObject(scenarioId)
		
		return None

def startScenario(scenario):
	ScenarioThread().startScenario(scenario)
	

def stopScenario():
	ScenarioThread()._stopScenarioEvent.set()

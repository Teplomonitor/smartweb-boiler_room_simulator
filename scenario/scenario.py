'''
@author: admin
'''

import os
from os.path import dirname, join

from pydoc import importfile
import time
import threading
import datetime

import main
import mainThread

from functions.limit import limit
from functions.timeOnDelay  import TimeOnDelay
from functions.periodicTrigger import PeriodicTrigger
from consoleLog import printLog   as printLog
from consoleLog import printError as printError


class Scenario(object):
	RELAY_OFF = 0
	RELAY_ON  = 255
	RELAY_MIN = 1
	RELAY_MAX = 254
	
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
	
	
	def simple_wait(self, delay):
		time.sleep(delay)
		return True
	
	def delay_with_break_check(self, delay):
		i = 0
		STEP = 1
		while i < delay:
			if self.is_stopped():
				return False
		
			i += STEP
			time.sleep(STEP)
		
		return True
	
	# don't do anything for "delay" seconds
	def wait(self, delay):
		if delay < 3: return self.simple_wait(delay)
		else        : return self.delay_with_break_check(delay)
	
	# wait for event() to become True
	def wait_event(self, event, timeout, arg = None, eventCheckPeriod = 1):
		timeoutDelay = TimeOnDelay()
		
		while True:
			if self.wait(eventCheckPeriod) == False:
				return False
			
			if arg is None:
				result = event()
			else:
				result = event(arg)
			
			if result:
				return True
			
			if timeoutDelay.get(True, timeout):
				return False
			
	# wait for the state() remain True for "duration" time
	def wait_state_permanence(self, state, duration, timeout = 0):
		if timeout:
			result = self.wait_event(state, timeout)
			if not result:
				return False
		
		waitDelay = TimeOnDelay()
		
		while True:
			if self.wait(1) == False:
				return False
			
			result = state()
			
			if not result:
				return False
			
			if waitDelay.get(True, duration):
				return True
	
	# wait to make sure value is same as setpoint
	# this function used to check how accurate program can control setpoint
	def wait_value_maintaining(self
							, valueHandler               # value we need to sustain (i.e. heating circuit temperature)
							, requiredValueHandler       # required value (i.e. required temperature) 
							, duration  = 10*60          # check duration. Value inside bounds should be at least this time to pass test
							, timeout   = 30*60          # value out of range timeout
							, dtTimeout = 2*60           # average error timeout
							, dtAvrMax  = 3              # max average error
							, dtMax     = 5              # max absolute error
							, supplyValueHandler = None  # value of the source that give us supply (i.e. boiler temperature)
							):
		
		bigDtDelay         = TimeOnDelay()
		checkTrigger       = PeriodicTrigger()
		flowControlTimeout = TimeOnDelay()
		flowControlTimer   = TimeOnDelay()
		
		dtAvr = 0
		dtAvrSource = 0
		a = 0.1
		b = 1 - a
		checkPeriod = 10
		
		while True:
			if self.wait(1) == False:
				return False
			
			temp       = valueHandler()
			tReq = requiredValueHandler()
			
			
			dt = temp - tReq
			dtAvr = dt*a + dtAvr*b
			
			if supplyValueHandler:
				sourceTemp = supplyValueHandler()
				dtSource = sourceTemp - tReq
				dtAvrSource = dtSource*a + dtAvrSource*b
				
				if dtAvrSource < 0:
					dtAvrMax = -dtAvrSource + 5
				else:
					dtAvrMax = limit(3, dtAvrSource/2, 10)
			
			
			if checkTrigger.get(checkPeriod):
				printLog(f'Среднее расхождение {dtAvr:.1f} ({dtAvrMax:.1f})')
				
			if flowControlTimer.get(abs(dtAvr) < dtAvrMax, duration):
				return True
			
			if bigDtDelay.get(abs(dt) > dtMax, dtTimeout):
				printError(f'Проблема! Слишком большое расхождение ({dt} > {dtMax})')
				return False
			
			if flowControlTimeout.get(True, timeout):
				printError(f'Проблема! Программа не смогла удержать параметр в допустимых пределах ({dtAvrMax})')
				return False
	
	
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
		if self._stopScenarioEvent.is_set():
			return None
		
		scenario = self.getScenario(self._scenarioIndex)
		self._scenarioIndex += 1
		return scenario
	
	def saveScenarioLog(self, scenario):
		programList = self._controllerHost.getProgramList()
		now = datetime.datetime.now()
		date_time = now.strftime("%Y-%m-%d_%H_%M")
		logDir = date_time + '_' + scenario.getScenarioTitle().replace(" ", "_")
		for prg in programList:
			prg.saveLog(logDir)
			
	def run(self):
		while mainThread.taskEnable():
			if self._newScenario:
				self.startScenarioNow(self._newScenario)
				self._newScenario = None
			
			if self._currentScenario:
				self._currentScenario.run()

				if self._currentScenario.done():
					self.appendScenarioResult(self._currentScenario)
					if self._currentScenario.getStatus() != 'OK':
						self.saveScenarioLog(self._currentScenario)
						
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

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
				
		printLog(f'starting {self.get_scenario_title()}')
		printLog(f'description: {self.get_scenario_description()}')
		
		self._manualSensorsList = []
	
		self.init_scenario()
		
	def get_scenario_title(self):
		return 'scenario'
	
	def get_scenario_description(self):
		return 'default'
	
	def get_checklist_id(self):
		return '--'
	
	def get_duration(self):
		return time.time() - self._startTime
	
	def set_manual(self, sensor, manual):
		sensor.set_manual(manual)
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
	
	
	def set_sensor_value(self, sensor, value):
		self.set_manual(sensor, True)
		sensor.setValue(value, True)
		
	def done(self):
		return self._status != 'IN_PROGRESS'
	
	def clear(self):
		for prg in self._programList.values():
			prg.enable_gui_control()
			
		for sensor in self._manualSensorsList:
			sensor.set_manual(False)
	
	def get_status(self):
		return self._status
	
	def init_scenario(self):
		ok = self.init_program_list(self.get_required_programs())
				
		if not ok:
			main.loadPreset(self.get_default_preset())
			
			while main.loadPresetDone() == False:
				self.wait(1)
			
			self.wait(2)
			
			if not self.init_program_list(self.get_required_programs()):
				printError('fail to init program list!')
			else:
				printLog('init ok!')
				ok = True
				
		if ok:
			for prg in self._programList.values():
				prg.disable_gui_control()
				
		self._startTime = time.time()

	def get_required_programs(self):
		requiredProgramTypesList = {
		}
		return requiredProgramTypesList
		
	def get_default_preset(self):
		return 'default'
	
	def init_program_list(self, requiredProgramTypesList):
		self._programList = {}
		for prgKey in requiredProgramTypesList:
			prg = self.get_unbinded_program(requiredProgramTypesList[prgKey])
			if prg is None:
				printError(f'{prgKey} not in program list!')
				self._programList = {}
				return False
			else:
				self._programList[prgKey] = prg
		return True
		
	def get_program_list(self):
		return self._controllerHost.get_program_list()
	
	def find_program_in_list(self, program):
		return [_ for _, prg in self._programList.items() if prg == program]
	
	def get_unbinded_program(self, programType):
		programsList = self.get_program_list()
		for program in programsList:
			if program.get_type() == programType:
				# in case we need to different programs of the same type
				if self.find_program_in_list(program):
					#this one already in list
					continue
				else:
					return program
		return None

def get_scenario_dir():
	return join(dirname(__file__),'list')

def get_scenario_files_list():
	__all__ = []
	
	def add_scenario_items(scenarioDir):
		def filter_scenario_items():
			if '__pycache__' in dirs : dirs .remove('__pycache__')  # don't visit __pycache__ directories
			if '__init__.py' in files: files.remove('__init__.py')  # don't use __init__.py files
			
		for root, dirs, files in os.walk(scenarioDir):
			filter_scenario_items()
			
			for scenarioFile in files:
				__all__.append(join(scenarioDir, scenarioFile))
				
			for scenarioSubDir in dirs:
				add_scenario_items(os.path.join(scenarioDir, scenarioSubDir))
				
			break
			
	
	add_scenario_items(get_scenario_dir())
	
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
		self._scenarioList = get_scenario_files_list()
		self._initDone = True
		
		self.daemon = True
		self.start()
	
	def getStopScenarioEvent(self):
		return self._stopScenarioEvent
	
	def getNextScenario(self):
		if self._stopScenarioEvent.is_set():
			return None
		
		scenario = self.get_scenario(self._scenarioIndex)
		self._scenarioIndex += 1
		return scenario
	
	def saveScenarioLog(self, scenario):
		programList = self._controllerHost.get_program_list()
		now = datetime.datetime.now()
		date_time = now.strftime("%Y-%m-%d_%H_%M")
		logDir = date_time + '_' + scenario.get_scenario_title().replace(" ", "_")
		for prg in programList:
			prg.save_log(logDir)
			
	def run(self):
		while mainThread.taskEnable():
			if self._newScenario:
				self.start_scenario_now(self._newScenario)
				self._newScenario = None
			
			if self._currentScenario:
				self._currentScenario.run()

				if self._currentScenario.done():
					self.append_scenario_result(self._currentScenario)
					if self._currentScenario.get_status() != 'OK':
						self.saveScenarioLog(self._currentScenario)
						
					self._currentScenario.clear()
					self._currentScenario = self.getNextScenario()
					if self._currentScenario == None:
						self.print_scenario_run_result()
							
			if self._stopScenarioEvent.is_set():
				self._stopScenarioEvent.clear()
				if self._currentScenario:
					printError(f'Сцераний прерван по внешнему запросу')
					self._currentScenario.clear()
					self._currentScenario = None
					self.print_scenario_run_result()
					
			time.sleep(1)
			
	def append_scenario_result(self, scenario):
		result = {
			'checklistId': scenario.get_checklist_id(),
			'result'     : scenario.get_status(),
			'duration'   : scenario.get_duration()
		}
		self._scenarioResultList.append(result)
		
	def print_scenario_run_result(self):
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
				
	def start_scenario(self, scenario):
		self._newScenario = scenario
	
	def start_scenario_now(self, scenario):
		self._scenarioStartTime = time.time()
		self._scenarioResultList = []
		
		if scenario == 'all':
			self._scenarioIndex = 0
			self._currentScenario = self.getNextScenario()
			return
		
		__all__ = self._scenarioList
		
		if scenario in __all__:
			self._scenarioIndex   = len(__all__)
			self._currentScenario = self.get_scenario_object(scenario)
		else:
			printError(f'{scenario} not in scenario list!')
			
	
	def get_scenario_object(self, scenarioId):
		scenario_module = importfile(scenarioId)
		return scenario_module.Scenario(self._controllerHost, self._simulator)

	def get_scenario(self, scenarioIndex):
		__all__ = self._scenarioList
		
		if scenarioIndex < len(__all__): 
			scenarioId = __all__[scenarioIndex]
			return self.get_scenario_object(scenarioId)
		
		return None

def start_scenario(scenario):
	ScenarioThread().start_scenario(scenario)
	

def stop_scenario():
	ScenarioThread()._stopScenarioEvent.set()

'''
@author: admin
'''

import time
import threading


def printLog(log_str):
	print(log_str)

def printError(log_str):
	print(log_str)

class Scenario_1():
	def __init__(self, programList):
		printLog('starting scenario 1')
		self._programsList = programList
		self._done = False
		self._snowmelterProgram = self.getProgramByType('SNOWMELT')
		if self._snowmelterProgram is None:
			self._done = True
			printError('Snowmelter not in program list!')
	
	def getProgramByType(self, programType):
		for program in self._programsList:
			if program.getType() == programType:
				return program
		
		return None
		
	def run(self):
		if self.done():
			return
		pass
	
	def done(self):
		return self._done


class ScenarioThread(threading.Thread):
	'''
	classdocs
	'''


	def __init__(self, controllerHost):
		'''
		Constructor
		'''
		self._controllerHost = controllerHost
		self._programsList   = self._controllerHost.getProgramList()
		
		self._currentScenario = self.getNextScenario()
		
	def getNextScenario(self):
		return Scenario_1(self._programsList)
		
	def run(self):
		while True:
			self._currentScenario.run()
			
			if self._currentScenario.done():
				self._currentScenario = self.getNextScenario()
				if self._currentScenario == None:
					return 0
				
			time.sleep(1)
			
			
			

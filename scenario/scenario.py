'''
@author: admin
'''
from os.path import dirname, basename, isfile, join
import glob

import time
import threading


def printLog(log_str):
	print(log_str)

def printError(log_str):
	print(log_str)


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


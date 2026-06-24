'''
@author: admin
'''

from consoleLog import printLog   as printLog
from consoleLog import printError as printError
from scenario.scenario import Scenario   as Parent

class Scenario(Parent):
	
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._pool   = self._programList['pool']

	def getScenarioTitle(self): return 'pool test 1'
	
	def getScenarioDescription(self):
		return 'Программа видит температуру воды в бассейне'
	
	def getChecklistId(self): return '3.11.1'
	
	def getRequiredPrograms(self):
		requiredProgramTypesList = {
			'pool'   : 'POOL',
		}
		return requiredProgramTypesList
	
	def getDefaultPreset(self): return 'swimmingPool'

	def readRequiredPoolTemperatureValue(self): return self._pool.readParameterValue('currentRequiredPoolTemperature')
	def getLoadingPumpState(self): return self._pool.getLoadingPumpState().getValue()
	
	def loadingPumpIsOn (self): return self.getLoadingPumpState() != self.RELAY_OFF
	def loadingPumpIsOff(self): return not self.loadingPumpIsOn()
	
	def setPoolTemperature(self, value):
		t = self._pool.getTemperature()
		self.setSensorValue(t, value)
	
	
	def run(self):
		printLog('читаем требуемую температуру бассейна')
		poolSetpoint = self.readRequiredPoolTemperatureValue()
		
		if poolSetpoint is None:
			self._status = 'FAIL'
			printError('Проблема! не удалось получить уставку бассейна')
			return
		
		self.wait(1)
		
		poolHysteresis = 1
		
		printLog('делаем подходящую для бассейна температуру')
		self.setPoolTemperature(poolSetpoint + poolHysteresis + 0.5)
		self.wait(1)

		printLog('Ждём, что насос загрузки выключится')
		pumpSwitchOffTimeout = 60
		if self.wait_event(self.loadingPumpIsOff, pumpSwitchOffTimeout):
			printLog('Хорошо, насос выключен')
		else:
			self._status = 'FAIL'
			printError('Плохо, насос не выключается')
			return
		self.wait(1)
		
		printLog('делаем в бассейне холодную температуру')
		self.setPoolTemperature(poolSetpoint - poolHysteresis - 0.5)
		self.wait(1)
		
		printLog(f'ждём когда насос загрузки включится')
		self.wait(1)
		
		pumpSwitchOnTimeout = 60
		if self.wait_event(self.loadingPumpIsOn, pumpSwitchOnTimeout):
			printLog('Хорошо! Бассейн видит температуру воды, и реагирует на неё')
			self._status = 'OK'
		else:
			printError('Плохо, не включается')
			self._status = 'FAIL'
		


'''
@author: admin
'''

import time

from consoleLog import printLog   as printLog
from consoleLog import printError as printError
from scenario.scenario import Scenario   as Parent
import functions.trigger as ft

from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay

def approx_Equal(x, y, tolerance=0.1):
	return abs(x-y) <= tolerance * (x + y) * 0.5

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._pool   = self._programList['pool']

	def getScenarioTitle(self): return 'pool test 2'
	
	def getScenarioDescription(self):
		return 'Программа управляет насосом циркуляции в зависимости от заданной программы'
	
	def getChecklistId(self): return '3.11.2'
	
	def getRequiredPrograms(self):
		requiredProgramTypesList = {
			'pool'   : 'POOL',
		}
		return requiredProgramTypesList
	
	def getDefaultPreset(self): return 'swimmingPool'

	def readRequiredPoolTemperatureValue(self): return self._pool.readParameterValue('currentRequiredPoolTemperature')
	def readCirculationPumpWorkPeriodOn (self): return self._pool.readParameterValue('circulationPumpWorkPeriodOn')
	def readCirculationPumpWorkPeriodOff(self): return self._pool.readParameterValue('circulationPumpWorkPeriodOff')
	def writeCirculationPumpWorkPeriodOn (self, value): return self._pool.writeParameterValue('circulationPumpWorkPeriodOn' , value)
	def writeCirculationPumpWorkPeriodOff(self, value): return self._pool.writeParameterValue('circulationPumpWorkPeriodOff', value)
	
	def getLoadingPumpState    (self): return self._pool.getLoadingPumpState().getValue()
	def getCirculationPumpState(self): return self._pool.getCirculationPumpState().getValue()
	
	def setPoolTemperature(self, value):
		t = self._pool.getTemperature()
		self.setSensorValue(t, value)
	
	def setCirculationPumpWorkMode(self, mode):
		printLog(f'делаем режим насоса {mode}')
		result = self._pool.setCirculationPumpWorkMode(mode)
		if result == None:
			printError('Плохо, не удалось задать режим работы насоса циркуляции')
			self._status = 'FAIL'
			return False
		
		return True
	
		
	
	def waitPumpSwitchOn(self, delay):
		timeoutDelay = TimeOnDelay()
		
		pump = False
		
		while True:
			if self.wait(1) == False:
				return False
			
			pump = self.getLoadingPumpState()
			if pump:
				break
			
			if timeoutDelay.Get(True, delay):
				return False
			
		return True
	
	def waitPumpSwitchOff(self, delay):
		timeoutDelay = TimeOnDelay()
		
		while True:
			if self.wait(1) == False:
				return False
			
			pump = self.getLoadingPumpState()
			
			if pump == False:
				break
			
			if timeoutDelay.Get(True, delay):
				return False
			
		return True
	
	def waitCirculationPumpWorking(self, delay, timeout):
		checkDelay   = TimeOnDelay()
		timeoutDelay = TimeOnDelay()
			
		while True:
			if self.wait(1) == False:
				return False
			
			pump = self.getCirculationPumpState()
			
			if checkDelay.Get(pump, delay):
				return True
			
			if timeoutDelay.Get(True, timeout):
				return False
			
		return True
	
	def waitCirculationPumpNotWorking(self, delay, timeout):
		checkDelay   = TimeOnDelay()
		timeoutDelay = TimeOnDelay()
			
		while True:
			if self.wait(1) == False:
				return False
			
			pump = self.getCirculationPumpState()
			
			if checkDelay.Get(pump == False, delay):
				return True
			
			if timeoutDelay.Get(True, timeout):
				return False
			
		return True
	
	def checkCirculationPumpWorkDuringHeatingPeriod(self):
		printLog('читаем требуемую температуру бассейна')
		poolSetpoint = self.readRequiredPoolTemperatureValue()
		
		if poolSetpoint is None:
			self._status = 'FAIL'
			printError('Проблема! не удалось получить уставку бассейна')
			return False

		self.wait(1)
		
		printLog('пока насос загрузки работает, насос циркуляции должен работать постоянно')
		# но насос загрузки не включится, если насос циркуляции выключен, т.к.
		# нельзя греть воду без циркуляции
		
		self.wait(1)
		
		poolHysteresis = 1
				
		printLog('делаем в бассейне холодную температуру')
		self.setPoolTemperature(poolSetpoint - poolHysteresis - 0.5)
		self.wait(1)
		
		printLog(f'проверяем работу насоса циркуляции при разных режимах')
		self.wait(1)

		circulationPumpWorkCheckDuration = 2*60
		circulationPumpWorkCheckTimeout  = 4*60
		
		workModes = [
			'CIRCULATION_ON'    ,
			'CIRCULATION_PROG'  ,
			'CIRCULATION_PERIOD',
			'CIRCULATION_OFF'   ,
			]
		
		
		for mode in workModes:
			if self.setCirculationPumpWorkMode(mode) == False:
				self._status = 'FAIL'
				return False
				
			result = self.waitCirculationPumpWorking(circulationPumpWorkCheckDuration, circulationPumpWorkCheckTimeout)
			if result:
				printLog('Хорошо, насос циркуляции работает')
				self._status = 'OK'
			else:
				printError('Плохо, насос циркуляции не включается')
				self._status = 'FAIL'
				return False
		
		return True

	def checkCirculationOnWorkMode(self):
		mode = 'CIRCULATION_ON'
		if self.setCirculationPumpWorkMode(mode) == False:
			self._status = 'FAIL'
			return False
			
		circulationPumpWorkCheckDuration = 2*60
		circulationPumpWorkCheckTimeout  = 4*60
		
		result = self.waitCirculationPumpWorking(circulationPumpWorkCheckDuration, circulationPumpWorkCheckTimeout)
		if result:
			printLog('Хорошо, насос циркуляции работает')
			self._status = 'OK'
		else:
			printError('Плохо, насос циркуляции не включается')
			self._status = 'FAIL'
			return False
		
		return True
	
	def checkCirculationOffWorkMode(self):
		mode = 'CIRCULATION_OFF'
		if self.setCirculationPumpWorkMode(mode) == False:
			self._status = 'FAIL'
			return False
			
		circulationPumpWorkCheckDuration = 2*60
		circulationPumpWorkCheckTimeout  = 4*60
		
		result = self.waitCirculationPumpNotWorking(circulationPumpWorkCheckDuration, circulationPumpWorkCheckTimeout)
		if result:
			printLog('Хорошо, насос циркуляции не работает')
			self._status = 'OK'
		else:
			printError('Плохо, насос циркуляции работает')
			self._status = 'FAIL'
			return False
		
		return True
		
	def checkCirculationPeriodicWorkMode(self):
		mode = 'CIRCULATION_PERIOD'
		if self.setCirculationPumpWorkMode(mode) == False:
			self._status = 'FAIL'
			return False
		
#		periodOn  = self.readCirculationPumpWorkPeriodOn ()
#		periodOff = self.readCirculationPumpWorkPeriodOff()
		
		periodOn  = 2*60
		periodOff = 3*60
		
		if self.writeCirculationPumpWorkPeriodOn (periodOn ) == None:
			printError('Плохо, не удалось задать длительность включения')
			self._status = 'FAIL'
			return False
			
		if self.writeCirculationPumpWorkPeriodOff(periodOff) == None:
			printError('Плохо, не удалось задать длительность выключения')
			self._status = 'FAIL'
			return False
			
		self.writeCirculationPumpWorkPeriodOff(periodOff)
		
		if (periodOn == None) or (periodOff == None):
			return False
		
		printLog(f'Период работы {periodOn}/{periodOff}')
		
		repeatTestCount = 5
		testDuration = (periodOn + periodOff) * repeatTestCount
		
		periodOnHyst  = periodOn/10
		periodOffHyst = periodOff/10
		
		onDelay  = TimeOnDelay()
		offDelay = TimeOnDelay()
		onTrigger = ft.RisingEdgeTrigger()
		offTrigger = ft.FallingEdgeTrigger()
		
		onTime = None
		offTime = None
		
		testStart = time.time()
		
		while True:
			if self.wait(1) == False:
				self._status = 'INTERRUPT'
				return False
			
			if time.time() - testStart > testDuration:
				break
			
			pump = self.getCirculationPumpState()
			
			if onDelay.Get(pump, periodOn + periodOnHyst):
				printError('Плохо, насос циркуляции работает слишком долго')
				self._status = 'FAIL'
				return False
			
			if offDelay.Get(not pump, periodOff + periodOffHyst):
				printError('Плохо, насос циркуляции выключен слишком долго')
				self._status = 'FAIL'
				return False
			
			if onTrigger .Get(pump):
				onTime  = time.time()
				if offTime:
					dt = onTime - offTime
					if approx_Equal(dt, periodOff):
						printLog('Хорошо, насос циркуляции включился на заданное время')
					else:
						printError(f'Плохо, период выключения насоса циркуляции неверный ({dt} != {periodOff})')
						self._status = 'FAIL'
						return False
						
			if offTrigger.Get(pump):
				offTime = time.time()
				if onTime:
					dt = offTime - onTime
					if approx_Equal(dt, periodOn):
						printLog('Хорошо, насос циркуляции выключился на заданное время')
					else:
						printError(f'Плохо, период включения насоса циркуляции неверный ({dt} != {periodOn})')
						self._status = 'FAIL'
						return False
				
		return True
		
	def checkCirculationPumpWorkDuringIdlePeriod(self):
		printLog('читаем требуемую температуру бассейна')
		poolSetpoint = self.readRequiredPoolTemperatureValue()
		
		if poolSetpoint is None:
			self._status = 'FAIL'
			printError('Проблема! не удалось получить уставку бассейна')
			return False

		self.wait(1)
		
		printLog('пока бассейн нагрет, насос циркуляции должен работать согласно своему режиму')
		self.wait(1)
		
		poolHysteresis = 1
				
		printLog('делаем подходящую для бассейна температуру')
		self.setPoolTemperature(poolSetpoint + poolHysteresis + 0.5)
		self.wait(1)

		printLog('Ждём, что насос загрузки выключится')
		pumpSwitchOffTimeout = 60
		
		if self.waitPumpSwitchOff(pumpSwitchOffTimeout):
			printLog('Хорошо, насос выключен')
		else:
			self._status = 'FAIL'
			printError('Плохо, насос не выключается')
			return False
		
		if self.checkCirculationPeriodicWorkMode() == False: return False
		if self.checkCirculationOnWorkMode      () == False: return False
		if self.checkCirculationOffWorkMode     () == False: return False
		
		return True
		

	def run(self):
		result = self.checkCirculationPumpWorkDuringIdlePeriod()
		if result == False:
			return

		result = self.checkCirculationPumpWorkDuringHeatingPeriod()
		if result == False:
			return



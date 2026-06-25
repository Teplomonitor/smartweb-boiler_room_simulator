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
	
	def loadingPumpIsOn (self): return self.getLoadingPumpState() != self.RELAY_OFF
	def loadingPumpIsOff(self): return self.getLoadingPumpState() == self.RELAY_OFF
	
	def circulationPumpIsOn (self): return self.getCirculationPumpState() != self.RELAY_OFF
	def circulationPumpIsOff(self): return self.getCirculationPumpState() == self.RELAY_OFF
	
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

		circulationPumpWorkCheckDuration = 5*60
		circulationPumpWorkCheckTimeout  = 30
		
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
				
			if not self.wait_state_permanence(self.circulationPumpIsOn, circulationPumpWorkCheckDuration, circulationPumpWorkCheckTimeout):
				printError('Плохо, насос циркуляции не работает')
				self._status = 'FAIL'
				return False
				
		
		printLog('Хорошо, во всех режимах насос циркуляции работает, пока идёт нагрев')
		self.wait(1)
		
		return True

	def checkCirculationOnWorkMode(self):
		printLog('Проверяем, что насос циркуляции включен на постоянку')
		self.wait(1)
		
		mode = 'CIRCULATION_ON'
		if self.setCirculationPumpWorkMode(mode) == False:
			printError('Плохо, не удалось задать режим работы')
			self._status = 'FAIL'
			return False
			
		circulationPumpWorkCheckDuration = 5*60
		circulationPumpWorkCheckTimeout  = 30
		
		if not self.wait_state_permanence(self.circulationPumpIsOn, circulationPumpWorkCheckDuration, circulationPumpWorkCheckTimeout):
			printError('Плохо, насос циркуляции выключается')
			self._status = 'FAIL'
			return False
			
		
		printLog('Хорошо, насос циркуляции работает продолжительное время')
		self._status = 'OK'
		
		return True
	
	def checkCirculationOffWorkMode(self):
		printLog('Проверяем, что насос циркуляции постоянно выключен')
		self.wait(1)
		
		mode = 'CIRCULATION_OFF'
		if self.setCirculationPumpWorkMode(mode) == False:
			printError('Плохо, не удалось задать режим работы')
			self._status = 'FAIL'
			return False
			
		circulationPumpWorkCheckDuration = 5*60
		circulationPumpWorkCheckTimeout  = 30
		
		if not self.wait_state_permanence(self.circulationPumpIsOff, circulationPumpWorkCheckDuration, circulationPumpWorkCheckTimeout):
			printError('Плохо, насос циркуляции включился')
			self._status = 'FAIL'
			return False
		
		printLog('Хорошо, насос циркуляции не работает')
		self._status = 'OK'
		
		return True
		
	def checkCirculationScheduleWorkMode(self):
		mode = 'CIRCULATION_PROG'
		if self.setCirculationPumpWorkMode(mode) == False:
			self._status = 'FAIL'
			return False
			

		# прочитать текущее время на контроллере
		# задать расписание насоса циркуляции, на каждый день разное
		# проверить, что насос включится и выключится в заданное на сегодня время
		return True
		
	def checkCirculationPeriodicWorkMode(self):
		printLog('Проверяем, что насос циркуляции работает импульсами заданной длины')
		self.wait(1)
		
		mode = 'CIRCULATION_PERIOD'
		if self.setCirculationPumpWorkMode(mode) == False:
			printError('Плохо, не удалось задать режим работы')
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
			
			pump = self.circulationPumpIsOn()
			
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
		pumpSwitchOffDuration = 5*60
		
		if self.wait_state_permanence(self.loadingPumpIsOff, pumpSwitchOffDuration, pumpSwitchOffTimeout):
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



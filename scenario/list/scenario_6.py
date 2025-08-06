'''
@author: admin
'''

import time

from consoleLog import printLog   as printLog
from consoleLog import printError as printError
from scenario.scenario import Scenario   as Parent

from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay
from functions.periodicTrigger import PeriodicTrigger

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._tptValve = self._programList['tptValve']
		self._valvePos = 0
		self._valveCheckTrigger = PeriodicTrigger()

	def getScenarioTitle(self): return 'scenario 6'
	
	def getScenarioDescription(self):
		return 'проверить, что программа "Смеситель" корректно переводит входной аналоговый сигнал в управление сигналами на открытие и закрытие смесителя'
	
	def getChecklistId(self): return '3.10.1'
	
	def getRequiredPrograms(self):
		requiredProgramTypesList = {
			'tptValve': 'TPT_VALVE_ADAPTER',
		}
		return requiredProgramTypesList
	
	def getDefaultPreset(self): return 'tptValve'

	def setControlSignal(self, value):
		t = self._tptValve.getControlSignal()
		self.setSensorValue(t, value)

	def getValveOpenState (self): return self._tptValve.getValveOpenOutput ().getValue()
	def getValveCloseState(self): return self._tptValve.getValveCloseOutput().getValue()
	
	def getValveState(self):
		valveOpen  = self.getValveOpenState()
		valveClose = self.getValveCloseState()
		
		if valveOpen and valveClose:
			printError('Проблема! Подаётся сигнал сразу на оба направления')
			return 'error'
		
		if valveOpen : return 'opening'
		if valveClose: return 'closing'
		
		return 'stop'
	
	def computeValvePos(self):
		if self._valveCheckTrigger.Get(1) == False:
			return self._valvePos
		
		valve = self.getValveState()
		
		valveRunningTime = 120
		step = 100 / valveRunningTime
		
		if   valve == 'closing': self._valvePos -= step
		elif valve == 'opening': self._valvePos += step
		
		self._valvePos = limit(0, self._valvePos, 100)
		
		return self._valvePos
		
	def waitValveClose(self, delay, timeout):
		valveClosingDelay = TimeOnDelay()
		testTimeoutDelay  = TimeOnDelay()
		
		while True:
			if self.wait(1) == False:
				return False
			
			valve = self.computeValvePos()
			if valveClosingDelay.Get(valve < 10, delay):
				return True
			
			if testTimeoutDelay.Get(True, timeout):
				return False
		return False
	
		
	def waitValveOpen(self, delay, timeout):
		valveOpeningDelay = TimeOnDelay()
		testTimeoutDelay  = TimeOnDelay()
		
		while True:
			if self.wait(1) == False:
				return False
			
			valve = self.computeValvePos()
			if valveOpeningDelay.Get(valve > 90, delay):
				return True
			
			if testTimeoutDelay.Get(True, timeout):
				printError(f'Слишком большой рассинхрон! 100 -> {valve:.1f} ')
				return False
		return False
	
	def valveSlowClosing(self, targetState):
		valveTestStopDelay = TimeOnDelay()
		valve = self.computeValvePos()
		signal = valve
		signalStep = 1
		
		while True:
			if self.wait(1) == False:
				return False
			valvePos = self.computeValvePos()
			self.setControlSignal(signal)
			
			if signal < targetState:
				signalStep = 0
				
			if valveTestStopDelay.Get(True, 120):
				ds = signal - valvePos
				if abs(ds) < 20:
					printLog(f'Ok! {signal} -> {valvePos:.1f}')
					return True
				else:
					printError(f'Слишком большой рассинхрон! {signal} -> {valvePos:.1f} ')
					return False
			
			signal -= signalStep
			
	def valveSlowOpening(self, targetState):
		valveTestStopDelay = TimeOnDelay()
		valve = self.computeValvePos()
		signal   = valve
		signalStep = 1
		
		while True:
			if self.wait(1) == False:
				return False
			
			valvePos = self.computeValvePos()
			self.setControlSignal(signal)
			
			if signal > targetState:
				signalStep = 0
				
			if valveTestStopDelay.Get(True, 120):
				ds = signal - valvePos
				if abs(ds) < 20:
					printLog(f'Ok! {signal} -> {valvePos:.1f}')
					return True
				else:
					printError(f'Слишком большой рассинхрон! {signal} -> {valvePos:.1f} ')
					return False
			
			signal += signalStep
		
	def valveHalt(self, targetState):
		valveTestStopDelay = TimeOnDelay()
		
		signal = targetState
		self.setControlSignal(signal)
		
		while True:
			if self.wait(1) == False:
				return False
			
			valvePos = self.computeValvePos()
			if valveTestStopDelay.Get(True, 60):
				ds = signal - valvePos
				if abs(ds) < 20:
					printLog(f'Ok! {signal} -> {valvePos:.1f}')
					return True
				else:
					printError(f'Слишком большой рассинхрон! {signal} -> {valvePos:.1f} ')
					return False
			
			
	def run(self):
		printLog('Подаём сигнал на полное закрытие смесителя')
		self.setControlSignal(0)
		if self.waitValveClose(20, 100) == False:
			printError('Проблема! Кран не закрывается полностью!')
			self._status = 'FAIL'
			return
			
		printLog('Подаём сигнал на открытие смесителя наполовину')
		if self.valveSlowOpening(self._valvePos + 50) == False:
			printError('Проблема! Кран открыт не наполовину!')
			self._status = 'FAIL'
			return
		
		printLog('Подаём сигнал на полное открытие смесителя')
		self.setControlSignal(100)
		if self.waitValveOpen(20, 100) == False:
			printError('Проблема! Кран не открывается полностью!')
			self._status = 'FAIL'
			return
			
		printLog('Подаём сигнал на закрытие смесителя наполовину')
		if self.valveSlowClosing(self._valvePos - 50) == False:
			printError('Проблема! Кран закрыт не наполовину!')
			self._status = 'FAIL'
			return
		
		printLog('Не меняем сигнал')
		if self.valveHalt(self._valvePos) == False:
			printError('Проблема! Кран двигается!')
			self._status = 'FAIL'
			return
		
		printLog('Test Ok!')
		self._status = 'OK'
		


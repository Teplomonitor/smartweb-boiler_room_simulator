'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.scenario import Scenario   as Parent

from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay
from functions.periodicTrigger import PeriodicTrigger
from functions.limit import limit


class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._tptValve = self._programList['tptValve']
		self._valvePos = 0
		self._valveCheckTrigger = PeriodicTrigger()

	def get_scenario_title(self): return 'scenario 6'
	
	def get_scenario_description(self):
		return 'проверить, что программа "Смеситель" корректно переводит входной аналоговый сигнал в управление сигналами на открытие и закрытие смесителя'
	
	def get_checklist_id(self): return '3.10.1'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'tptValve': 'TPT_VALVE_ADAPTER',
		}
		return requiredProgramTypesList
	
	def get_default_preset(self): return 'tptValve'

	def setControlSignal(self, value):
		t = self._tptValve.getControlSignal()
		self.set_sensor_value(t, value)

	def getValveOpenState (self): return self._tptValve.getValveOpenOutput ().get_value()
	def getValveCloseState(self): return self._tptValve.getValveCloseOutput().get_value()
	
	def getValveState(self):
		valveOpen  = self.getValveOpenState()
		valveClose = self.getValveCloseState()
		
		if valveOpen and valveClose:
			print_error('Проблема! Подаётся сигнал сразу на оба направления')
			return 'error'
		
		if valveOpen : return 'opening'
		if valveClose: return 'closing'
		
		return 'stop'
	
	def computeValvePos(self):
		if self._valveCheckTrigger.get(1) == False:
			return self._valvePos
		
		valve = self.getValveState()
		
		valveRunningTime = 120
		step = 100 / valveRunningTime
		
		if   valve == 'closing': self._valvePos -= step
		elif valve == 'opening': self._valvePos += step
		
		self._valvePos = limit(0, self._valvePos, 100)
		
		return self._valvePos
	
	def valveIsClose(self):
		valve = self.computeValvePos()
		return valve < 10
	
	def valveIsOpen(self):
		valve = self.computeValvePos()
		return valve > 90
	
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
				
			if valveTestStopDelay.get(True, 120):
				ds = signal - valvePos
				if abs(ds) < 20:
					print_log(f'Ok! {signal} -> {valvePos:.1f}')
					return True
				else:
					print_error(f'Слишком большой рассинхрон! {signal} -> {valvePos:.1f} ')
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
				
			if valveTestStopDelay.get(True, 120):
				ds = signal - valvePos
				if abs(ds) < 20:
					print_log(f'Ok! {signal} -> {valvePos:.1f}')
					return True
				else:
					print_error(f'Слишком большой рассинхрон! {signal} -> {valvePos:.1f} ')
					return False
			
			signal += signalStep
	
	def valveHalt(self, targetPos):
		self.setControlSignal(targetPos)
		
		
		def getRequiredValue():
			return targetPos
		
		result = self.wait_value_maintaining(
			self.computeValvePos,
			getRequiredValue,
			60, 2*60, 20,
			5, 10
			)
		
		valvePos = self.computeValvePos()
		
		if result:
			print_log(f'Ok! {targetPos} -> {valvePos:.1f}')
			return True
		else:
			print_error(f'Слишком большой рассинхрон! {targetPos} -> {valvePos:.1f} ')
			return False
			
			
	def run(self):
		print_log('Подаём сигнал на полное закрытие смесителя')
		self.setControlSignal(0)
		if self.wait_state_permanence(self.valveIsClose, 60, 100) == False:
			print_error('Проблема! Кран не закрывается полностью!')
			self._status = 'FAIL'
			return
			
		print_log('Подаём сигнал на открытие смесителя наполовину')
		if self.valveSlowOpening(self._valvePos + 50) == False:
			print_error('Проблема! Кран открыт не наполовину!')
			self._status = 'FAIL'
			return
		
		print_log('Подаём сигнал на полное открытие смесителя')
		self.setControlSignal(100)
		if self.wait_state_permanence(self.valveIsOpen, 60, 100) == False:
			print_error('Проблема! Кран не открывается полностью!')
			self._status = 'FAIL'
			return
			
		print_log('Подаём сигнал на закрытие смесителя наполовину')
		if self.valveSlowClosing(self._valvePos - 50) == False:
			print_error('Проблема! Кран закрыт не наполовину!')
			self._status = 'FAIL'
			return
		
		print_log('Не меняем сигнал')
		if self.valveHalt(50) == False:
			print_error('Проблема! Кран двигается!')
			self._status = 'FAIL'
			return
		
		print_log('Test Ok!')
		self._status = 'OK'
		


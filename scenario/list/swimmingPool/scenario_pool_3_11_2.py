'''
@author: admin
'''

import time

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.scenario import Scenario   as Parent
import functions.trigger as ft
import smartnet.constants as snc

from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay

def approx_Equal(x, y, tolerance=0.1):
	return abs(x-y) <= tolerance * (x + y) * 0.5

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._pool   = self._programList['pool']

	def get_scenario_title(self): return 'pool test 2'
	
	def get_scenario_description(self):
		return 'Программа управляет насосом циркуляции в зависимости от заданной программы'
	
	def get_checklist_id(self): return '3.11.2'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'pool'   : snc.ProgramType.POOL,
		}
		return requiredProgramTypesList
	
	def get_default_preset(self): return 'swimmingPool'

	def readRequiredPoolTemperatureValue(self): return self._pool.read_parameter_value('currentRequiredPoolTemperature')
	def readCirculationPumpWorkPeriodOn (self): return self._pool.read_parameter_value('circulationPumpWorkPeriodOn')
	def readCirculationPumpWorkPeriodOff(self): return self._pool.read_parameter_value('circulationPumpWorkPeriodOff')
	def writeCirculationPumpWorkPeriodOn (self, value): return self._pool.write_parameter_value('circulationPumpWorkPeriodOn' , value)
	def writeCirculationPumpWorkPeriodOff(self, value): return self._pool.write_parameter_value('circulationPumpWorkPeriodOff', value)
	
	def getLoadingPumpState    (self): return self._pool.getLoadingPumpState().get_value()
	def getCirculationPumpState(self): return self._pool.getCirculationPumpState().get_value()
	
	def loadingPumpIsOn (self): return self.getLoadingPumpState() != self.RELAY_OFF
	def loadingPumpIsOff(self): return self.getLoadingPumpState() == self.RELAY_OFF
	
	def circulationPumpIsOn (self): return self.getCirculationPumpState() != self.RELAY_OFF
	def circulationPumpIsOff(self): return self.getCirculationPumpState() == self.RELAY_OFF
	
	def setPoolTemperature(self, value):
		t = self._pool.get_temperature()
		self.set_sensor_value(t, value)
	
	def setCirculationPumpWorkMode(self, mode):
		print_log(f'делаем режим насоса {mode}')
		result = self._pool.setCirculationPumpWorkMode(mode)
		if result == None:
			print_error('Плохо, не удалось задать режим работы насоса циркуляции')
			self._status = 'FAIL'
			return False
		
		return True
	
	def checkCirculationPumpWorkDuringHeatingPeriod(self):
		print_log('читаем требуемую температуру бассейна')
		poolSetpoint = self.readRequiredPoolTemperatureValue()
		
		if poolSetpoint is None:
			self._status = 'FAIL'
			print_error('Проблема! не удалось получить уставку бассейна')
			return False

		self.wait(1)
		
		print_log('пока насос загрузки работает, насос циркуляции должен работать постоянно')
		# но насос загрузки не включится, если насос циркуляции выключен, т.к.
		# нельзя греть воду без циркуляции
		
		self.wait(1)
		
		poolHysteresis = 1
				
		print_log('делаем в бассейне холодную температуру')
		self.setPoolTemperature(poolSetpoint - poolHysteresis - 0.5)
		self.wait(1)
		
		print_log(f'проверяем работу насоса циркуляции при разных режимах')
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
				print_error('Плохо, насос циркуляции не работает')
				self._status = 'FAIL'
				return False
				
		
		print_log('Хорошо, во всех режимах насос циркуляции работает, пока идёт нагрев')
		self.wait(1)
		
		return True

	def checkCirculationOnWorkMode(self):
		print_log('Проверяем, что насос циркуляции включен на постоянку')
		self.wait(1)
		
		mode = 'CIRCULATION_ON'
		if self.setCirculationPumpWorkMode(mode) == False:
			print_error('Плохо, не удалось задать режим работы')
			self._status = 'FAIL'
			return False
			
		circulationPumpWorkCheckDuration = 5*60
		circulationPumpWorkCheckTimeout  = 30
		
		if not self.wait_state_permanence(self.circulationPumpIsOn, circulationPumpWorkCheckDuration, circulationPumpWorkCheckTimeout):
			print_error('Плохо, насос циркуляции выключается')
			self._status = 'FAIL'
			return False
			
		
		print_log('Хорошо, насос циркуляции работает продолжительное время')
		self._status = 'OK'
		
		return True
	
	def checkCirculationOffWorkMode(self):
		print_log('Проверяем, что насос циркуляции постоянно выключен')
		self.wait(1)
		
		mode = 'CIRCULATION_OFF'
		if self.setCirculationPumpWorkMode(mode) == False:
			print_error('Плохо, не удалось задать режим работы')
			self._status = 'FAIL'
			return False
			
		circulationPumpWorkCheckDuration = 5*60
		circulationPumpWorkCheckTimeout  = 30
		
		if not self.wait_state_permanence(self.circulationPumpIsOff, circulationPumpWorkCheckDuration, circulationPumpWorkCheckTimeout):
			print_error('Плохо, насос циркуляции включился')
			self._status = 'FAIL'
			return False
		
		print_log('Хорошо, насос циркуляции не работает')
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
		print_log('Проверяем, что насос циркуляции работает импульсами заданной длины')
		self.wait(1)
		
		mode = 'CIRCULATION_PERIOD'
		if self.setCirculationPumpWorkMode(mode) == False:
			print_error('Плохо, не удалось задать режим работы')
			self._status = 'FAIL'
			return False
		
#		periodOn  = self.readCirculationPumpWorkPeriodOn ()
#		periodOff = self.readCirculationPumpWorkPeriodOff()
		
		periodOn  = 2*60
		periodOff = 3*60
		
		if self.writeCirculationPumpWorkPeriodOn (periodOn ) == None:
			print_error('Плохо, не удалось задать длительность включения')
			self._status = 'FAIL'
			return False
			
		if self.writeCirculationPumpWorkPeriodOff(periodOff) == None:
			print_error('Плохо, не удалось задать длительность выключения')
			self._status = 'FAIL'
			return False
			
		print_log(f'Период работы {periodOn}/{periodOff}')
		
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
			
			if onDelay.get(pump, periodOn + periodOnHyst):
				print_error('Плохо, насос циркуляции работает слишком долго')
				self._status = 'FAIL'
				return False
			
			if offDelay.get(not pump, periodOff + periodOffHyst):
				print_error('Плохо, насос циркуляции выключен слишком долго')
				self._status = 'FAIL'
				return False
			
			if onTrigger .get(pump):
				onTime  = time.time()
				if offTime:
					dt = onTime - offTime
					if approx_Equal(dt, periodOff):
						print_log('Хорошо, насос циркуляции включился на заданное время')
					else:
						print_error(f'Плохо, период выключения насоса циркуляции неверный ({dt} != {periodOff})')
						self._status = 'FAIL'
						return False
						
			if offTrigger.get(pump):
				offTime = time.time()
				if onTime:
					dt = offTime - onTime
					if approx_Equal(dt, periodOn):
						print_log('Хорошо, насос циркуляции выключился на заданное время')
					else:
						print_error(f'Плохо, период включения насоса циркуляции неверный ({dt} != {periodOn})')
						self._status = 'FAIL'
						return False
				
		return True
		
	def checkCirculationPumpWorkDuringIdlePeriod(self):
		print_log('читаем требуемую температуру бассейна')
		poolSetpoint = self.readRequiredPoolTemperatureValue()
		
		if poolSetpoint is None:
			self._status = 'FAIL'
			print_error('Проблема! не удалось получить уставку бассейна')
			return False

		self.wait(1)
		
		print_log('пока бассейн нагрет, насос циркуляции должен работать согласно своему режиму')
		self.wait(1)
		
		poolHysteresis = 1
				
		print_log('делаем подходящую для бассейна температуру')
		self.setPoolTemperature(poolSetpoint + poolHysteresis + 0.5)
		self.wait(1)

		print_log('Ждём, что насос загрузки выключится')
		pumpSwitchOffTimeout = 60
		pumpSwitchOffDuration = 5*60
		
		if self.wait_state_permanence(self.loadingPumpIsOff, pumpSwitchOffDuration, pumpSwitchOffTimeout):
			print_log('Хорошо, насос выключен')
		else:
			self._status = 'FAIL'
			print_error('Плохо, насос не выключается')
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



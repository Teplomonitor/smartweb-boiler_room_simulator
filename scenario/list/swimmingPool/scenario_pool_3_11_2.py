'''
@author: admin
'''

import time

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.swimming_pool import PoolScenario
import functions.trigger as ft

from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay

def approx_equal(x, y, tolerance=0.1):
	return abs(x-y) <= tolerance * (x + y) * 0.5

class Scenario(PoolScenario):

	def get_scenario_title(self): return 'pool test 2'
	
	def get_scenario_description(self):
		return 'Программа управляет насосом циркуляции в зависимости от заданной программы'
	
	def get_checklist_id(self): return '3.11.2'
	
	def read_circulation_pump_work_period_on(self):
		return self._pool.read_parameter_value('circulationPumpWorkPeriodOn')

	def read_circulation_pump_work_period_off(self):
		return self._pool.read_parameter_value('circulationPumpWorkPeriodOff')

	def write_circulation_pump_work_period_on(self, value):
		return self._pool.write_parameter_value('circulationPumpWorkPeriodOn', value)

	def write_circulation_pump_work_period_off(self, value):
		return self._pool.write_parameter_value('circulationPumpWorkPeriodOff', value)
	
	def set_circulation_pump_work_mode(self, mode):
		print_log(f'делаем режим насоса {mode}')
		result = self._pool.setCirculationPumpWorkMode(mode)
		if result == None:
			print_error('Плохо, не удалось задать режим работы насоса циркуляции')
			self._status = 'FAIL'
			return False
		
		return True
	
	def check_circulation_pump_work_during_heating_period(self):
		print_log('читаем требуемую температуру бассейна')
		pool_setpoint = self.read_required_pool_temperature()
		
		if pool_setpoint is None:
			self._status = 'FAIL'
			print_error('Проблема! не удалось получить уставку бассейна')
			return False

		self.wait(1)
		
		print_log('пока насос загрузки работает, насос циркуляции должен работать постоянно')
		# но насос загрузки не включится, если насос циркуляции выключен, т.к.
		# нельзя греть воду без циркуляции
		
		self.wait(1)
		
		pool_hysteresis = 1
				
		print_log('делаем в бассейне холодную температуру')
		self.set_pool_temperature(pool_setpoint - pool_hysteresis - 0.5)
		self.wait(1)
		
		print_log(f'проверяем работу насоса циркуляции при разных режимах')
		self.wait(1)

		circulation_pump_work_check_duration = 5 * 60
		circulation_pump_work_check_timeout = 30
		
		workModes = [
			'CIRCULATION_ON'    ,
			'CIRCULATION_PROG'  ,
			'CIRCULATION_PERIOD',
			'CIRCULATION_OFF'   ,
			]
		
		
		for mode in workModes:
			if self.set_circulation_pump_work_mode(mode) == False:
				self._status = 'FAIL'
				return False
				
			if not self.wait_state_permanence(self.circulation_pump_is_on, circulation_pump_work_check_duration, circulation_pump_work_check_timeout):
				print_error('Плохо, насос циркуляции не работает')
				self._status = 'FAIL'
				return False
				
		
		print_log('Хорошо, во всех режимах насос циркуляции работает, пока идёт нагрев')
		self.wait(1)
		
		return True

	def check_circulation_on_work_mode(self):
		print_log('Проверяем, что насос циркуляции включен на постоянку')
		self.wait(1)
		
		mode = 'CIRCULATION_ON'
		if self.set_circulation_pump_work_mode(mode) == False:
			print_error('Плохо, не удалось задать режим работы')
			self._status = 'FAIL'
			return False
			
		circulation_pump_work_check_duration = 5 * 60
		circulation_pump_work_check_timeout = 30
		
		if not self.wait_state_permanence(self.circulation_pump_is_on, circulation_pump_work_check_duration, circulation_pump_work_check_timeout):
			print_error('Плохо, насос циркуляции выключается')
			self._status = 'FAIL'
			return False
			
		
		print_log('Хорошо, насос циркуляции работает продолжительное время')
		self._status = 'OK'
		
		return True
	
	def check_circulation_off_work_mode(self):
		print_log('Проверяем, что насос циркуляции постоянно выключен')
		self.wait(1)
		
		mode = 'CIRCULATION_OFF'
		if self.set_circulation_pump_work_mode(mode) == False:
			print_error('Плохо, не удалось задать режим работы')
			self._status = 'FAIL'
			return False
			
		circulation_pump_work_check_duration = 5 * 60
		circulation_pump_work_check_timeout = 30
		
		if not self.wait_state_permanence(self.circulation_pump_is_off, circulation_pump_work_check_duration, circulation_pump_work_check_timeout):
			print_error('Плохо, насос циркуляции включился')
			self._status = 'FAIL'
			return False
		
		print_log('Хорошо, насос циркуляции не работает')
		self._status = 'OK'
		
		return True
		
	def check_circulation_schedule_work_mode(self):
		mode = 'CIRCULATION_PROG'
		if self.set_circulation_pump_work_mode(mode) == False:
			self._status = 'FAIL'
			return False
			

		# прочитать текущее время на контроллере
		# задать расписание насоса циркуляции, на каждый день разное
		# проверить, что насос включится и выключится в заданное на сегодня время
		return True
		
	def check_circulation_periodic_work_mode(self):
		print_log('Проверяем, что насос циркуляции работает импульсами заданной длины')
		self.wait(1)
		
		mode = 'CIRCULATION_PERIOD'
		if self.set_circulation_pump_work_mode(mode) == False:
			print_error('Плохо, не удалось задать режим работы')
			self._status = 'FAIL'
			return False
		
#		periodOn  = self.readCirculationPumpWorkPeriodOn ()
#		periodOff = self.readCirculationPumpWorkPeriodOff()
		
		period_on = 1 * 60
		period_off = 2 * 60
		
		if self.write_circulation_pump_work_period_on(period_on) == None:
			print_error('Плохо, не удалось задать длительность включения')
			self._status = 'FAIL'
			return False
			
		if self.write_circulation_pump_work_period_off(period_off) == None:
			print_error('Плохо, не удалось задать длительность выключения')
			self._status = 'FAIL'
			return False
			
		print_log(f'Период работы {period_on}/{period_off}')
		
		repeat_test_count = 3
		test_duration = (period_on + period_off) * repeat_test_count
		
		period_on_hysteresis = period_on / 10
		period_off_hysteresis = period_off / 10
		
		on_delay = TimeOnDelay()
		off_delay = TimeOnDelay()
		on_trigger = ft.RisingEdgeTrigger()
		off_trigger = ft.FallingEdgeTrigger()
		
		on_time = None
		off_time = None
		
		test_start = time.time()
		
		while True:
			if self.wait(1) == False:
				self._status = 'INTERRUPT'
				return False
			
			if time.time() - test_start > test_duration:
				break
			
			pump = self.circulation_pump_is_on()
			
			if on_delay.get(pump, period_on + period_on_hysteresis):
				print_error('Плохо, насос циркуляции работает слишком долго')
				self._status = 'FAIL'
				return False
			
			if off_delay.get(not pump, period_off + period_off_hysteresis):
				print_error('Плохо, насос циркуляции выключен слишком долго')
				self._status = 'FAIL'
				return False
			
			if on_trigger.get(pump):
				on_time = time.time()
				if off_time:
					dt = on_time - off_time
					if approx_equal(dt, period_off):
						print_log('Хорошо, насос циркуляции включился на заданное время')
					else:
						print_error(f'Плохо, период выключения насоса циркуляции неверный ({dt} != {period_off})')
						self._status = 'FAIL'
						return False
						
			if off_trigger.get(pump):
				off_time = time.time()
				if on_time:
					dt = off_time - on_time
					if approx_equal(dt, period_on):
						print_log('Хорошо, насос циркуляции выключился на заданное время')
					else:
						print_error(f'Плохо, период включения насоса циркуляции неверный ({dt} != {period_on})')
						self._status = 'FAIL'
						return False
				
		return True
		
	def check_circulation_pump_work_during_idle_period(self):
		print_log('читаем требуемую температуру бассейна')
		pool_setpoint = self.read_required_pool_temperature()
		
		if pool_setpoint is None:
			self._status = 'FAIL'
			print_error('Проблема! не удалось получить уставку бассейна')
			return False

		self.wait(1)
		
		print_log('пока бассейн нагрет, насос циркуляции должен работать согласно своему режиму')
		self.wait(1)
		
		pool_hysteresis = 1
				
		print_log('делаем подходящую для бассейна температуру')
		self.set_pool_temperature(pool_setpoint + pool_hysteresis + 0.5)
		self.wait(1)

		print_log('Ждём, что насос загрузки выключится')
		pump_switch_off_timeout = 60
		pump_switch_off_duration = 5 * 60
		
		if self.wait_state_permanence(self.loading_pump_is_off, pump_switch_off_duration, pump_switch_off_timeout):
			print_log('Хорошо, насос выключен')
		else:
			self._status = 'FAIL'
			print_error('Плохо, насос не выключается')
			return False
		
		if self.check_circulation_periodic_work_mode() == False: return False
		if self.check_circulation_on_work_mode() == False: return False
		if self.check_circulation_off_work_mode() == False: return False
		
		return True
		

	def run(self):
		result = self.check_circulation_pump_work_during_idle_period()
		if result == False:
			return

		result = self.check_circulation_pump_work_during_heating_period()
		if result == False:
			return



'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.swimming_pool import PoolScenario

class Scenario(PoolScenario):

	def get_scenario_title(self): return 'pool test 1'
	
	def get_scenario_description(self):
		return 'Программа видит температуру воды в бассейне'
	
	def get_checklist_id(self): return '3.11.1'
	
	def run(self):
		print_log('читаем требуемую температуру бассейна')
		pool_setpoint = self.read_required_pool_temperature()
		
		if pool_setpoint is None:
			self._status = 'FAIL'
			print_error('Проблема! не удалось получить уставку бассейна')
			return
		
		self.wait(1)
		
		pool_hysteresis = 1
		
		print_log('делаем подходящую для бассейна температуру')
		self.set_pool_temperature(pool_setpoint + pool_hysteresis + 0.5)
		self.wait(1)

		print_log('Ждём, что насос загрузки выключится')
		pump_switch_off_timeout = 60
		if self.wait_event(self.loading_pump_is_off, pump_switch_off_timeout):
			print_log('Хорошо, насос выключен')
		else:
			self._status = 'FAIL'
			print_error('Плохо, насос не выключается')
			return
		self.wait(1)
		
		print_log('делаем в бассейне холодную температуру')
		self.set_pool_temperature(pool_setpoint - pool_hysteresis - 0.5)
		self.wait(1)
		
		print_log(f'ждём когда насос загрузки включится')
		self.wait(1)
		
		pump_switch_on_timeout = 60
		if self.wait_event(self.loading_pump_is_on, pump_switch_on_timeout):
			print_log('Хорошо! Бассейн видит температуру воды, и реагирует на неё')
			self._status = 'OK'
		else:
			print_error('Плохо, не включается')
			self._status = 'FAIL'
		


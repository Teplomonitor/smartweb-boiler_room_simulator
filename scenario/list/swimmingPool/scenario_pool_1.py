'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.scenario import Scenario   as Parent

class Scenario(Parent):
	
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._pool   = self._programList['pool']

	def get_scenario_title(self): return 'pool test 1'
	
	def get_scenario_description(self):
		return 'Программа видит температуру воды в бассейне'
	
	def get_checklist_id(self): return '3.11.1'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'pool'   : 'POOL',
		}
		return requiredProgramTypesList
	
	def get_default_preset(self): return 'swimmingPool'

	def readRequiredPoolTemperatureValue(self): return self._pool.read_parameter_value('currentRequiredPoolTemperature')
	def getLoadingPumpState(self): return self._pool.getLoadingPumpState().get_value()
	
	def loadingPumpIsOn (self): return self.getLoadingPumpState() != self.RELAY_OFF
	def loadingPumpIsOff(self): return not self.loadingPumpIsOn()
	
	def setPoolTemperature(self, value):
		t = self._pool.get_temperature()
		self.set_sensor_value(t, value)
	
	
	def run(self):
		print_log('читаем требуемую температуру бассейна')
		poolSetpoint = self.readRequiredPoolTemperatureValue()
		
		if poolSetpoint is None:
			self._status = 'FAIL'
			print_error('Проблема! не удалось получить уставку бассейна')
			return
		
		self.wait(1)
		
		poolHysteresis = 1
		
		print_log('делаем подходящую для бассейна температуру')
		self.setPoolTemperature(poolSetpoint + poolHysteresis + 0.5)
		self.wait(1)

		print_log('Ждём, что насос загрузки выключится')
		pumpSwitchOffTimeout = 60
		if self.wait_event(self.loadingPumpIsOff, pumpSwitchOffTimeout):
			print_log('Хорошо, насос выключен')
		else:
			self._status = 'FAIL'
			print_error('Плохо, насос не выключается')
			return
		self.wait(1)
		
		print_log('делаем в бассейне холодную температуру')
		self.setPoolTemperature(poolSetpoint - poolHysteresis - 0.5)
		self.wait(1)
		
		print_log(f'ждём когда насос загрузки включится')
		self.wait(1)
		
		pumpSwitchOnTimeout = 60
		if self.wait_event(self.loadingPumpIsOn, pumpSwitchOnTimeout):
			print_log('Хорошо! Бассейн видит температуру воды, и реагирует на неё')
			self._status = 'OK'
		else:
			print_error('Плохо, не включается')
			self._status = 'FAIL'
		


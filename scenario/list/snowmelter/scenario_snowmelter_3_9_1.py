'''
@author: admin
'''


from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.snowmelter import SnowmelterScenario   as Parent


class Scenario(Parent):
	def get_scenario_title(self): return 'scenario 1'

	def get_scenario_description(self):
		return 'check if circulation pump switch off, if T < TfrostProtect'

	def get_checklist_id(self): return '3.9.1'

	def run(self):
		plateSetpoint = self.readRequiredPlateTemperatureValue()
		
		if plateSetpoint is None:
			self._status = 'FAIL'
			print_error('Проблема! не удалось получить уставку плиты')
			return
		
		tFrostProtect = self.readFrostProtectionTemperatureValue()
		
		if tFrostProtect is None:
			self._status = 'FAIL'
			print_error('Test fail! Can\'t get frost protect temp')
			return
		
		print_log('делаем подходящую для снеготайки уличную температуру')
		if self.setMediumOutdoorTemperature() == False:
			print_error('Проблема! Не удалось задать уличную температуру')
			self._status = 'FAIL'
			return
		
		self.wait(3)
		
		print_log('делаем плиту холодной')
		self.setPlateTemperature(plateSetpoint - 2)
		self.wait(3)
		
		print_log('Warm up')
		self.wait(30)
		
		print_log('Waiting for circulation pump to switch on')
		if self.wait_event(self.circulationPumpIsOn, 60):
			print_log('ok, cirulation pump is working')
		else:
			self._status = 'FAIL'
			print_error('Test fail! Pump don\'t work')
			return
			
		self.wait(2)
		
		print_log('making "cold" backward flow temperature')
		self.setBacwardFlowTemperature(tFrostProtect - 1)
		
		pumpSwitchOffDuration = 5*60
		pumpSwitchOffTimeout  = 2*60
		
		print_log(f'Waiting for circulation pump to switch off for at least {pumpSwitchOffDuration} seconds')
		
		if self.wait_state_permanence(self.circulationPumpIsOff, pumpSwitchOffDuration, pumpSwitchOffTimeout):
			print_log('Test Ok!')
			self._status = 'OK'
		else:
			print_error('Test fail! Pump don\'t switch off')
			self._status = 'FAIL'
		


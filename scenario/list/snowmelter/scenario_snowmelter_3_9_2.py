'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.snowmelter import SnowmelterScenario   as Parent

class Scenario(Parent):
	def get_scenario_title(self):
		return 'scenario 2'

	def get_scenario_description(self):
		return 'проверить, что насос циркуляции выключается, если температура плиты выше требуемой больше, чем на 2 градуса'

	def get_checklist_id(self):
		return '3.9.2'

	def run(self):
		plateSetpoint = self.readRequiredPlateTemperatureValue()
		
		if plateSetpoint is None:
			self._status = 'FAIL'
			print_error('Проблема! не удалось получить уставку плиты')
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
		
		print_log('ждём, пока система устаканится')
		if self.wait(30) == False:
			return
		
		print_log('ждём, когда насос циркуляции включится')
		if self.wait_event(self.circulationPumpIsOn, 60):
			print_log('Хорошо, включился')
		else:
			self._status = 'FAIL'
			print_error('Плохо. Не включился!')
			return
			
		self.wait(2)
		
		print_log('делаем плиту горячей')
		self.setPlateTemperature(plateSetpoint + 2.1)
		
		pumpSwitchOffDuration = 5*60
		pumpSwitchOffTimeout  = 2*60
		
		print_log(f'Ждём, пока насос циркуляции не выключится хотя бы на {pumpSwitchOffDuration} секунд')
		
		if self.wait_state_permanence(self.circulationPumpIsOff, pumpSwitchOffDuration, pumpSwitchOffTimeout):
			print_log('Хорошо!')
			self._status = 'OK'
		else:
			print_error('Плохо. Насос не выключается!')
			self._status = 'FAIL'
		


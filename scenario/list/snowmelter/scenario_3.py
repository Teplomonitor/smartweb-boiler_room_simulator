'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.snowmelter import SnowmelterScenario   as Parent

class Scenario(Parent):
	def get_scenario_title(self):
		return 'scenario 3'

	def get_scenario_description(self):
		return 'проверить, что снеготайка не работает, если уличная температура выше или ниже заданного диапазона (задержка 5 минут)'

	def get_checklist_id(self):
		return '3.9.3'

	def outdoorTemperatureIsHot(self, maxValue):
		oat = self.readSnowmelterOutdoorTemperature()
		return oat > maxValue

	def outdoorTemperatureIsCold(self, minValue):
		oat = self.readSnowmelterOutdoorTemperature()
		return oat < minValue

	def setHighOutdoorTemperature(self):
		maxTemp = self.readMaxOutdoorTemperature()
		self.setOutdoorTemperature(maxTemp + 5)
		return self.wait_event(self.outdoorTemperatureIsHot, 5*60, maxTemp)

	def setLowOutdoorTemperature(self):
		minTemp = self.readMinOutdoorTemperature()
		self.setOutdoorTemperature(minTemp - 5)
		return self.wait_event(self.outdoorTemperatureIsCold, 5*60, minTemp)

	def run(self):
		plateSetpoint = self.readRequiredPlateTemperatureValue()
		
		if plateSetpoint is None:
			print_error('Проблема! не удалось получить уставку плиты')
			self._status = 'FAIL'
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
		self.wait(30)
		
		print_log('ждём, когда насос циркуляции включится')
		if self.wait_event(self.circulationPumpIsOn, 60):
			print_log('Хорошо, включился')
		else:
			self._status = 'FAIL'
			print_error('Плохо. Не включился!')
			return
			
		self.wait(2)
		
		print_log('делаем на улице жарко')
		if self.setHighOutdoorTemperature() == False:
			print_log('Плохо! Снеготайка не видит, что на улице жарко!')
			self._status = 'FAIL'
			return
		
		pumpsSwitchOffTestDuration = 5*60
		
		print_log(f'Ждём, пока насосы не выключатся хотя бы на {pumpsSwitchOffTestDuration} секунд')
		
		pumpsSwitchOffDelay = 5*60
		testExtraDelay      = 60
		timeout = pumpsSwitchOffDelay + pumpsSwitchOffTestDuration + testExtraDelay
		
		if self.wait_state_permanence(self.pumpsAreOff, pumpsSwitchOffTestDuration, timeout):
			print_log('Хорошо!')
		else:
			print_error('Плохо. Насосы не выключаются!')
			self._status = 'FAIL'
			return
		
		print_log('снова делаем подходящую для снеготайки уличную температуру')
		self.setMediumOutdoorTemperature()
		self.wait(3)

		print_log('ждём, пока система устаканится')
		self.wait(30)
		
		print_log('ждём, когда насос циркуляции включится')
		if self.wait_event(self.circulationPumpIsOn, 60):
			print_log('Хорошо, включился')
		else:
			self._status = 'FAIL'
			print_error('Плохо. Не включился!')
			return
			
		self.wait(2)
		
		print_log('делаем на улице холодно')
		if self.setLowOutdoorTemperature() == False:
			print_log('Плохо! Снеготайка не видит, что на улице холодно!')
			self._status = 'FAIL'
			return
		
		print_log(f'Ждём, пока насосы не выключатся хотя бы на {pumpsSwitchOffTestDuration} секунд')
		
		if self.wait_state_permanence(self.pumpsAreOff, pumpsSwitchOffTestDuration, timeout):
			print_log('Хорошо!')
			self._status = 'OK'
		else:
			print_error('Плохо. Насосы не выключаются!')
			self._status = 'FAIL'
		
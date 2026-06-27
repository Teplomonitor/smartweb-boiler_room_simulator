'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.scenario import Scenario   as Parent

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._snowmelter = self._programList['snowmelter']
		self._outdoor    = self._programList['oat']

	def get_scenario_title(self):
		return 'scenario 3'
	
	def get_scenario_description(self):
		return 'проверить, что снеготайка не работает, если уличная температура выше или ниже заданного диапазона (задержка 5 минут)'
	
	def get_checklist_id(self):
		return '3.9.3'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'snowmelter': 'SNOWMELT',
			'oat'       : 'OUTDOOR_SENSOR',
		}
		return requiredProgramTypesList
	
	def get_default_preset(self):
		return 'snowmelter'
		
		
	def readRequiredPlateTemperatureValue(self): return self._snowmelter.read_parameter_value('reqPlateTemp')
	def readMinOutdoorTemperature(self)        : return self._snowmelter.read_parameter_value('minOutdoorTemp')
	def readMaxOutdoorTemperature(self)        : return self._snowmelter.read_parameter_value('maxOutdoorTemp')
	def readSnowmelterOutdoorTemperature(self) : return self._snowmelter.read_parameter_value('outdoorTemp')
	def getCirculationPumpState(self):
		return self._snowmelter.getSecondaryPumpState().get_value()
	
	def circulationPumpIsOn (self): return self.getCirculationPumpState() != self.RELAY_OFF
	def circulationPumpIsOff(self): return self.getCirculationPumpState() == self.RELAY_OFF
	
	def getLoadingPumpState(self):
		return self._snowmelter.getPrimaryPumpState().get_value()
	
	def loadingPumpIsOn (self): return self.getLoadingPumpState() != self.RELAY_OFF
	def loadingPumpIsOff(self): return not self.loadingPumpIsOn()
	
	def pumpsAreOff(self): return self.loadingPumpIsOff() and self.circulationPumpIsOff()
	
	def setBacwardFlowTemperature(self, value):
		t = self._snowmelter.getBackwardFlowTemperature()
		self.set_sensor_value(t, value)
		
	def setPlateTemperature(self, value):
		t = self._snowmelter.getPlateTemperature()
		self.set_sensor_value(t, value)
		
	def setOutdoorTemperature(self, value):
		t = self._outdoor.getOutdoorTemperature()
		self.set_sensor_value(t, value)
		
	def outdoorTemperatureIsHot(self, maxValue):
		oat = self.readSnowmelterOutdoorTemperature()
		return oat > maxValue
	
	def outdoorTemperatureIsCold(self, minValue):
		oat = self.readSnowmelterOutdoorTemperature()
		return oat < minValue
	
	def setMediumOutdoorTemperature(self):
		minTemp = self.readMinOutdoorTemperature()
		maxTemp = self.readMaxOutdoorTemperature()
		
		if (minTemp == None) or (maxTemp == None):
			return False
		
		midTemp = (minTemp + maxTemp)/2
		self.setOutdoorTemperature(midTemp)
		return True

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
		
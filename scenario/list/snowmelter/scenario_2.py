'''
@author: admin
'''

from consoleLog import printLog   as printLog
from consoleLog import printError as printError
from scenario.scenario import Scenario   as Parent

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._snowmelter = self._programList['snowmelter']
		self._outdoor    = self._programList['oat']

	def get_scenario_title(self):
		return 'scenario 2'
	
	def get_scenario_description(self):
		return 'проверить, что насос циркуляции выключается, если температура плиты выше требуемой больше, чем на 2 градуса'
	
	def get_checklist_id(self):
		return '3.9.2'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'snowmelter': 'SNOWMELT',
			'oat'       : 'OUTDOOR_SENSOR',
		}
		return requiredProgramTypesList
	
	def get_default_preset(self):
		return 'snowmelter'
		
		
	def readRequiredPlateTemperatureValue(self): return self._snowmelter.readParameterValue('reqPlateTemp')
	def readMinOutdoorTemperature(self)        : return self._snowmelter.readParameterValue('minOutdoorTemp')
	def readMaxOutdoorTemperature(self)        : return self._snowmelter.readParameterValue('maxOutdoorTemp')
	
	def getCirculationPumpState(self):
		return self._snowmelter.getSecondaryPumpState().getValue()
	
	def circulationPumpIsOn (self): return self.getCirculationPumpState() != self.RELAY_OFF
	def circulationPumpIsOff(self): return self.getCirculationPumpState() == self.RELAY_OFF
	
	def setBacwardFlowTemperature(self, value):
		t = self._snowmelter.getBackwardFlowTemperature()
		self.set_sensor_value(t, value)
		
	def setPlateTemperature(self, value):
		t = self._snowmelter.getPlateTemperature()
		self.set_sensor_value(t, value)
		
	def setOutdoorTemperature(self, value):
		t = self._outdoor.getOutdoorTemperature()
		self.set_sensor_value(t, value)
		
	
	def setMediumOutdoorTemperature(self):
		minTemp = self.readMinOutdoorTemperature()
		maxTemp = self.readMaxOutdoorTemperature()
		
		if (minTemp == None) or (maxTemp == None):
			return False
		
		midTemp = (minTemp + maxTemp)/2
		self.setOutdoorTemperature(midTemp)
		return True

	def run(self):
		plateSetpoint = self.readRequiredPlateTemperatureValue()
		
		if plateSetpoint is None:
			self._status = 'FAIL'
			printError('Проблема! не удалось получить уставку плиты')
			return
		
		printLog('делаем подходящую для снеготайки уличную температуру')
		if self.setMediumOutdoorTemperature() == False:
			printError('Проблема! Не удалось задать уличную температуру')
			self._status = 'FAIL'
			return
		
		self.wait(3)
		
		printLog('делаем плиту холодной')
		self.setPlateTemperature(plateSetpoint - 2)
		self.wait(3)
		
		printLog('ждём, пока система устаканится')
		if self.wait(30) == False:
			return
		
		printLog('ждём, когда насос циркуляции включится')
		if self.wait_event(self.circulationPumpIsOn, 60):
			printLog('Хорошо, включился')
		else:
			self._status = 'FAIL'
			printError('Плохо. Не включился!')
			return
			
		self.wait(2)
		
		printLog('делаем плиту горячей')
		self.setPlateTemperature(plateSetpoint + 2.1)
		
		pumpSwitchOffDuration = 5*60
		pumpSwitchOffTimeout  = 2*60
		
		printLog(f'Ждём, пока насос циркуляции не выключится хотя бы на {pumpSwitchOffDuration} секунд')
		
		if self.wait_state_permanence(self.circulationPumpIsOff, pumpSwitchOffDuration, pumpSwitchOffTimeout):
			printLog('Хорошо!')
			self._status = 'OK'
		else:
			printError('Плохо. Насос не выключается!')
			self._status = 'FAIL'
		


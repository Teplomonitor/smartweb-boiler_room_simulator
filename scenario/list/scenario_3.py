'''
@author: admin
'''

import time

from consoleLog import printLog   as printLog
from consoleLog import printError as printError
from scenario.scenario import Scenario   as Parent

from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._snowmelter = self._programList['snowmelter']
		self._outdoor    = self._programList['oat']

	def getScenarioTitle(self):
		return 'scenario 3'
	
	def getScenarioDescription(self):
		return 'проверить, что снеготайка не работает, если уличная температура выше или ниже заданного диапазона (задержка 5 минут)'
	
	def getChecklistId(self):
		return '3.9.3'
	
	def getRequiredPrograms(self):
		requiredProgramTypesList = {
			'snowmelter': 'SNOWMELT',
			'oat'       : 'OUTDOOR_SENSOR',
		}
		return requiredProgramTypesList
	
	def getDefaultPreset(self):
		return 'snowmelter'
		
		
	def readRequiredPlateTemperatureValue(self): return self._snowmelter.readParameterValue('reqPlateTemp')
	def readMinOutdoorTemperature(self)        : return self._snowmelter.readParameterValue('minOutdoorTemp')
	def readMaxOutdoorTemperature(self)        : return self._snowmelter.readParameterValue('maxOutdoorTemp')
	
	def getCirculationPumpState(self):
		return self._snowmelter.getSecondaryPumpState().getValue()
	
	def getLoadingPumpState(self):
		return self._snowmelter.getPrimaryPumpState().getValue()
	
	def setBacwardFlowTemperature(self, value):
		t = self._snowmelter.getBackwardFlowTemperature()
		self.setSensorValue(t, value)
		
	def setPlateTemperature(self, value):
		t = self._snowmelter.getPlateTemperature()
		self.setSensorValue(t, value)
		
	def setOutdoorTemperature(self, value):
		t = self._outdoor.getOutdoorTemperature()
		self.setSensorValue(t, value)
		
	def waitPumpSwitchOn(self, delay):
		pumpNotWorkingDelay = TimeOnDelay()
		
		pump = False
		
		while not pump:
			time.sleep(1)
			
			pump = self.getCirculationPumpState()
			if pumpNotWorkingDelay.Get(not pump, delay):
				return False
			
		return True
	
	def waitPumpsSwitchOff(self, delay, timeout):
		pumpNotWorkingDelay = TimeOnDelay()
		testTimeoutDelay    = TimeOnDelay()
		
		while True:
			time.sleep(1)
			
			pump1 = self.getCirculationPumpState()
			pump2 = self.getLoadingPumpState()
			if pumpNotWorkingDelay.Get(not (pump1 or pump2), delay):
				return True
			
			if testTimeoutDelay.Get(True, timeout):
				return False
		return False
	
	def setMediumOutdoorTemperature(self):
		minTemp = self.readMinOutdoorTemperature()
		maxTemp = self.readMaxOutdoorTemperature()
		
		midTemp = (minTemp + maxTemp)/2
		self.setOutdoorTemperature(midTemp)

	def setHighOutdoorTemperature(self):
		maxTemp = self.readMaxOutdoorTemperature()
		self.setOutdoorTemperature(maxTemp + 1)
		
	def setLowOutdoorTemperature(self):
		minTemp = self.readMinOutdoorTemperature()
		self.setOutdoorTemperature(minTemp - 1)
		
	def run(self):
		plateSetpoint = self.readRequiredPlateTemperatureValue()
		
		if plateSetpoint is None:
			self._status = 'FAIL'
			printError('Проблема! не удалось получить уставку плиты')
			return
		
		printLog('делаем подходящую для снеготайки уличную температуру')
		self.setMediumOutdoorTemperature()
		time.sleep(3)
		
		printLog('делаем плиту холодной')
		self.setPlateTemperature(plateSetpoint - 2)
		time.sleep(3)
		
		printLog('ждём, пока система устаканится')
		time.sleep(30)
		
		printLog('ждём, пока насос циркуляции не включится')
		if self.waitPumpSwitchOn(60):
			printLog('Хорошо, включился')
		else:
			self._status = 'FAIL'
			printError('Плохо. Не включился!')
			return
			
		time.sleep(2)
		
		printLog('делаем на улице жарко')
		self.setHighOutdoorTemperature()
		
		pumpsSwitchOffDuration = 60
		
		printLog(f'Ждём, пока насосы не выключатся хотя бы на {pumpsSwitchOffDuration} секунд')
		time.sleep(10)
		
		if self.waitPumpsSwitchOff(pumpsSwitchOffDuration, 6*60):
			printLog('Хорошо!')
		else:
			printError('Плохо. Насосы не выключаются!')
			self._status = 'FAIL'
			return
		
		printLog('снова делаем подходящую для снеготайки уличную температуру')
		self.setMediumOutdoorTemperature()
		time.sleep(3)

		printLog('ждём, пока система устаканится')
		time.sleep(30)
				
		printLog('ждём, пока насос циркуляции не включится')
		if self.waitPumpSwitchOn(60):
			printLog('Хорошо, включился')
		else:
			self._status = 'FAIL'
			printError('Плохо. Не включился!')
			return
			
		time.sleep(2)
		
		printLog('делаем на улице холодно')
		self.setLowOutdoorTemperature()
		
		printLog(f'Ждём, пока насосы не выключатся хотя бы на {pumpsSwitchOffDuration} секунд')
		time.sleep(10)
		
		if self.waitPumpsSwitchOff(pumpsSwitchOffDuration, 6*60):
			printLog('Хорошо!')
			self._status = 'OK'
		else:
			printError('Плохо. Насосы не выключается!')
			self._status = 'FAIL'
		
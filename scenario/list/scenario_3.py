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
	def readSnowmelterOutdoorTemperature(self) : return self._snowmelter.readParameterValue('outdoorTemp')
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
			
			snowmelterIsWorking = (pump1 or pump2)
			if pumpNotWorkingDelay.Get(not snowmelterIsWorking, delay):
				return True
			
			if testTimeoutDelay.Get(snowmelterIsWorking, timeout):
				return False
		return False
	
	def waitOutdoorTemperatureSet(self, reqOat, condition, timeout):
		oatSetTimeoutDelay = TimeOnDelay()
		
		while True:
			time.sleep(5)
			
			oat = self.readSnowmelterOutdoorTemperature()
			
			if condition == 'more':
				if oat > reqOat:
					return True
			elif condition == 'less':
				if oat < reqOat:
					return True
				
			if oatSetTimeoutDelay.Get(True, timeout):
				return False
			
		return False
		
		
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
		self.setOutdoorTemperature(maxTemp + 1)
		return self.waitOutdoorTemperatureSet(maxTemp, 'more', 5*60)
			
		
	def setLowOutdoorTemperature(self):
		minTemp = self.readMinOutdoorTemperature()
		self.setOutdoorTemperature(minTemp - 1)
		return self.waitOutdoorTemperatureSet(minTemp, 'less', 5*60)
		
	def run(self):
		plateSetpoint = self.readRequiredPlateTemperatureValue()
		
		if plateSetpoint is None:
			printError('Проблема! не удалось получить уставку плиты')
			self._status = 'FAIL'
			return
		
		printLog('делаем подходящую для снеготайки уличную температуру')
		if self.setMediumOutdoorTemperature() == False:
			printError('Проблема! Не удалось задать уличную температуру')
			self._status = 'FAIL'
			return
		
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
		if self.setHighOutdoorTemperature() == False:
			printLog('Плохо! Снеготайка не видит, что на улице жарко!')
			self._status = 'FAIL'
			return
		
		pumpsSwitchOffTestDuration = 60
		
		printLog(f'Ждём, пока насосы не выключатся хотя бы на {pumpsSwitchOffTestDuration} секунд')
		time.sleep(10)
		
		pumpsSwitchOffDelay = 5*60
		testExtraDelay      = 60
		
		if self.waitPumpsSwitchOff(pumpsSwitchOffTestDuration, pumpsSwitchOffDelay + pumpsSwitchOffTestDuration + testExtraDelay):
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
		if self.setLowOutdoorTemperature() == False:
			printLog('Плохо! Снеготайка не видит, что на улице холодно!')
			self._status = 'FAIL'
			return
		
		printLog(f'Ждём, пока насосы не выключатся хотя бы на {pumpsSwitchOffTestDuration} секунд')
		time.sleep(10)
		
		if self.waitPumpsSwitchOff(pumpsSwitchOffTestDuration, pumpsSwitchOffDelay + pumpsSwitchOffTestDuration + testExtraDelay):
			printLog('Хорошо!')
			self._status = 'OK'
		else:
			printError('Плохо. Насосы не выключаются!')
			self._status = 'FAIL'
		
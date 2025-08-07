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
		self._pressure   = self._programList['pressure']

	def getScenarioTitle(self):
		return 'scenario 5'
	
	def getScenarioDescription(self):
		return 'проверить, что снеготайка выключает насосы загрузки и циркуляции, если получает сигнал об аварии от Аварийной программы'
	
	def getChecklistId(self):
		return '3.9.5'
	
	def getRequiredPrograms(self):
		requiredProgramTypesList = {
			'snowmelter': 'SNOWMELT',
			'oat'       : 'OUTDOOR_SENSOR',
			'pressure'  : 'FILLING_LOOP',
		}
		return requiredProgramTypesList
	
	def getDefaultPreset(self):
		return 'snowmelterWithPressureControl'
		
		
	def readRequiredPlateTemperatureValue(self): return self._snowmelter.readParameterValue('reqPlateTemp')
	def readMinOutdoorTemperature(self)        : return self._snowmelter.readParameterValue('minOutdoorTemp')
	def readMaxOutdoorTemperature(self)        : return self._snowmelter.readParameterValue('maxOutdoorTemp')
	def readSnowmelterOutdoorTemperature(self) : return self._snowmelter.readParameterValue('outdoorTemp')
	def readRequiredFlowTemperature(self)      : return self._snowmelter.readParameterValue('reqFlowTemp')
	
	def getDirectFlowTemperature(self): return self._snowmelter.getDirectFlowTemperature().getValue()
	
	def getCirculationPumpState(self):
		return self._snowmelter.getSecondaryPumpState().getValue()
	
	def getLoadingPumpState(self):
		return self._snowmelter.getPrimaryPumpState().getValue()
	
	def setPlateTemperature(self, value):
		t = self._snowmelter.getPlateTemperature()
		self.setSensorValue(t, value)
		
	def setOutdoorTemperature(self, value):
		t = self._outdoor.getOutdoorTemperature()
		self.setSensorValue(t, value)
		
	def waitOutdoorTemperatureSet(self, reqOat, condition, timeout):
		oatSetTimeoutDelay = TimeOnDelay()
		
		while True:
			self.wait(5)
			
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
		
	def waitPumpSwitchOn(self, delay):
		pumpNotWorkingDelay = TimeOnDelay()
		
		pump = False
		
		while not pump:
			if self.wait(1) == False:
				return False
			
			pump = self.getCirculationPumpState()
			if pumpNotWorkingDelay.Get(not pump, delay):
				return False
			
		return True
	
	def waitPumpsSwitchOff(self, delay, timeout):
		pumpNotWorkingDelay = TimeOnDelay()
		testTimeoutDelay    = TimeOnDelay()
		
		while True:
			if self.wait(1) == False:
				return False
			
			pump1 = self.getCirculationPumpState()
			pump2 = self.getLoadingPumpState()
			
			snowmelterIsWorking = (pump1 or pump2)
			if pumpNotWorkingDelay.Get(not snowmelterIsWorking, delay):
				return True
			
			if testTimeoutDelay.Get(snowmelterIsWorking, timeout):
				return False
		return False
	
	def setAlarmSignal(self, value):
		t = self._pressure.getPressure()
		state = 'open' if value else 'short'
		self.setSensorValue(t, state)
		
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
		
		self.wait(3)
		
		printLog('делаем плиту холодной')
		self.setPlateTemperature(plateSetpoint - 2)
		self.wait(3)
		
		printLog('ждём, пока система устаканится')
		self.wait(30)
		
		printLog('ждём, пока насос циркуляции не включится')
		if self.waitPumpSwitchOn(60):
			printLog('Хорошо, включился')
		else:
			self._status = 'FAIL'
			printError('Плохо. Не включился!')
			return
			
		self.wait(2)
		
		printLog('включаем сигнал низкого давление в программе подпитки')
		self.setAlarmSignal(True)
		
		pumpsSwitchOffTestDuration = 60
		
		printLog(f'Ждём, пока насосы не выключатся хотя бы на {pumpsSwitchOffTestDuration} секунд')
		self.wait(10)
				
		pumpsSwitchOffDelay = 60
		testExtraDelay      = 60
		
		if self.waitPumpsSwitchOff(pumpsSwitchOffTestDuration, pumpsSwitchOffDelay + pumpsSwitchOffTestDuration + testExtraDelay):
			printLog('Хорошо!')
			self._status = 'OK'
		else:
			printError('Плохо. Насосы не выключаются!')
			self._status = 'FAIL'



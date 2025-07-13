'''
@author: admin
'''

import time

from consoleLog import printLog   as printLog
from consoleLog import printError as printError
from scenario.scenario import Scenario   as Parent

from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay
from functions.periodicTrigger  import PeriodicTrigger  as PeriodicTrigger

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._snowmelter = self._programList['snowmelter']
		self._outdoor    = self._programList['oat']

	def getScenarioTitle(self):
		return 'scenario 4'
	
	def getScenarioDescription(self):
		return 'проверить, что насос загрузки поддерживает заданную температуру на выходе из теплообменника'
	
	def getChecklistId(self):
		return '3.9.4'
	
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
	
	def checkFlowTemperatureControl(self):
		tReq = self.readRequiredFlowTemperature()
		
		bigDtDelay         = TimeOnDelay()
		flowControlTimeout = TimeOnDelay()
		flowControlTimer   = TimeOnDelay()
		checkTrigger       = PeriodicTrigger()
		
		checkPeriod         = 10
		bigDtTimeout        = 60
		flowControlDuration = 10*60
		maxCheckDuration    = 30*60
		
		dtAvrMax = 3
		dtMax = 5
		
		dtAvr = 0
		a = 0.1
		b = 1 - a
		
		while True:
			time.sleep(1)
			
			temp = self.getDirectFlowTemperature()
			dt = temp - tReq
			dtAvr = dt*a + dtAvr*b
			
			if checkTrigger.Get(checkPeriod):
				printLog(f'Средняя разница температур {dtAvr:.1f}K')
				
			if flowControlTimer.Get(abs(dtAvr) < dtAvrMax, flowControlDuration):
				return True
			
			if bigDtDelay.Get(abs(dt) > dtMax, bigDtTimeout):
				printError(f'Проблема! Слишком большая разница температур ({dt} > {dtMax})')
				return False
			
			if flowControlTimeout.Get(True, maxCheckDuration):
				printError(f'Проблема! Слишком большая средняя разница температур ({dtAvr:.1f} > {dtAvrMax})')
				return False
			
	
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
		
		
		result = self.checkFlowTemperatureControl()
		
		if result:
			self._status = 'OK'
		else:
			self._status = 'FAIL'


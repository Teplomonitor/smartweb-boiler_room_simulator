'''
@author: admin
'''

import time

from consoleLog import printLog   as printLog
from consoleLog import printError as printError
from scenario.scenario import Scenario   as Parent

from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay
from functions.periodicTrigger  import PeriodicTrigger  as PeriodicTrigger
from functions.limit import limit

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
		
	def getSourceTemperature(self):
		return self._sim._collector.getDirectTemperature()

		
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
		
		self.waitOutdoorTemperatureSet(maxTemp, 'less', 5*60)
		self.waitOutdoorTemperatureSet(minTemp, 'more', 5*60)
		
		return True

	def getAverageValue(self, array, period):
		pass
	
	def checkFlowTemperatureControl(self):
		tReq = self.readRequiredFlowTemperature()
		
		bigDtDelay         = TimeOnDelay()
		flowControlTimeout = TimeOnDelay()
		flowControlTimer   = TimeOnDelay()
		checkTrigger       = PeriodicTrigger()
		
		checkPeriod         = 10
		bigDtTimeout        = 4*60
		flowControlDuration = 10*60
		maxCheckDuration    = 30*60
		
		dtAvrMax = 3
		dtMax = 5
		
		dtAvr = 0
		dtAvrSource = 0
		a = 0.1
		b = 1 - a
		
#		tempArray = []
#		sourceTempArray = []
#		timeArray = []
		
		
		while True:
			if self.wait(1) == False:
				return False
			
#			now = time.time()

			temp       = self.getDirectFlowTemperature()
			sourceTemp = self.getSourceTemperature()
			
			
#			tempArray      .append(temp)
#			sourceTempArray.append(sourceTemp)
#			timeArray      .append(now)
			
			
			dt = temp - tReq
			dtAvr = dt*a + dtAvr*b
			
			dtSource = sourceTemp - tReq
			dtAvrSource = dtSource*a + dtAvrSource*b
			
			if dtAvrSource < 0:
				dtAvrMax = -dtAvrSource + 5
			else:
				dtAvrMax = limit(3, dtAvrSource/2, 10)
			
			
			if checkTrigger.Get(checkPeriod):
				printLog(f'Средняя разница температур {dtAvr:.1f}K ({dtAvrMax:.1f})')
				
			if flowControlTimer.Get(abs(dtAvr) < dtAvrMax, flowControlDuration):
				return True
			
			if bigDtDelay.Get(abs(dt) > dtMax, bigDtTimeout):
				printError(f'Проблема! Слишком большая разница температур ({dt} > {dtMax})')
				return False
			
			if flowControlTimeout.Get(True, maxCheckDuration):
				printError(f'Проблема! Программа не смогла удержать температуру в допустимых пределах ({dtAvrMax}K)')
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
		
		self.wait(3)
		
		printLog('делаем плиту холодной')
		self.setPlateTemperature(plateSetpoint - 2)
		self.wait(3)
		
		printLog('ждём, пока система устаканится')
		self.wait(30)
		
		
		result = self.checkFlowTemperatureControl()
		
		if result:
			self._status = 'OK'
		else:
			self._status = 'FAIL'


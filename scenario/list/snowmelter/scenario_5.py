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

	def get_scenario_title(self):
		return 'scenario 5'
	
	def get_scenario_description(self):
		return 'проверить, что снеготайка выключает насосы загрузки и циркуляции, если получает сигнал об аварии от Аварийной программы'
	
	def get_checklist_id(self):
		return '3.9.5'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'snowmelter': 'SNOWMELT',
			'oat'       : 'OUTDOOR_SENSOR',
			'pressure'  : 'FILLING_LOOP',
		}
		return requiredProgramTypesList
	
	def get_default_preset(self):
		return 'snowmelterWithPressureControl'
		
		
	def readRequiredPlateTemperatureValue(self): return self._snowmelter.readParameterValue('reqPlateTemp')
	def readMinOutdoorTemperature(self)        : return self._snowmelter.readParameterValue('minOutdoorTemp')
	def readMaxOutdoorTemperature(self)        : return self._snowmelter.readParameterValue('maxOutdoorTemp')
	def readSnowmelterOutdoorTemperature(self) : return self._snowmelter.readParameterValue('outdoorTemp')
	def readRequiredFlowTemperature(self)      : return self._snowmelter.readParameterValue('reqFlowTemp')
	
	def getDirectFlowTemperature(self): return self._snowmelter.getDirectFlowTemperature().getValue()
	
	def getCirculationPumpState(self):
		return self._snowmelter.getSecondaryPumpState().getValue()
	
	def circulationPumpIsOn (self): return self.getCirculationPumpState() != self.RELAY_OFF
	def circulationPumpIsOff(self): return self.getCirculationPumpState() == self.RELAY_OFF
	
	def getLoadingPumpState(self):
		return self._snowmelter.getPrimaryPumpState().getValue()
	
	def loadingPumpIsOn (self): return self.getLoadingPumpState() != self.RELAY_OFF
	def loadingPumpIsOff(self): return not self.loadingPumpIsOn()
	
	def pumpsAreOff(self): return self.loadingPumpIsOff() and self.circulationPumpIsOff()
	
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
		
	def setAlarmSignal(self, value):
		t = self._pressure.getPressure()
		state = 'open' if value else 'short'
		self.set_sensor_value(t, state)
		
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
		
		printLog('ждём, когда насос циркуляции включится')
		if self.wait_event(self.circulationPumpIsOn, 60):
			printLog('Хорошо, включился')
		else:
			self._status = 'FAIL'
			printError('Плохо. Не включился!')
			return
			
		self.wait(2)
		
		printLog('включаем сигнал низкого давление в программе подпитки')
		self.setAlarmSignal(True)
		
		pumpsSwitchOffTestDuration = 5*60
		
		printLog(f'Ждём, пока насосы не выключатся хотя бы на {pumpsSwitchOffTestDuration} секунд')
		self.wait(10)
				
		pumpsSwitchOffDelay = 60
		testExtraDelay      = 60
		timeout = pumpsSwitchOffDelay + pumpsSwitchOffTestDuration + testExtraDelay

		if self.wait_state_permanence(self.pumpsAreOff, pumpsSwitchOffTestDuration, timeout):
			printLog('Хорошо!')
			self._status = 'OK'
		else:
			printError('Плохо. Насосы не выключаются!')
			self._status = 'FAIL'



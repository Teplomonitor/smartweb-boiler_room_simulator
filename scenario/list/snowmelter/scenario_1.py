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

	def get_scenario_title(self): return 'scenario 1'
	
	def get_scenario_description(self):
		return 'check if circulation pump switch off, if T < TfrostProtect'
	
	def get_checklist_id(self): return '3.9.1'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'snowmelter': 'SNOWMELT',
			'oat'       : 'OUTDOOR_SENSOR',
		}
		return requiredProgramTypesList
	
	def get_default_preset(self): return 'snowmelter'

	def readFrostProtectionTemperatureValue(self): return self._snowmelter.readParameterValue('frostProtectionTemp')
	def readRequiredPlateTemperatureValue(self)  : return self._snowmelter.readParameterValue('reqPlateTemp')
	def readMinOutdoorTemperature(self)          : return self._snowmelter.readParameterValue('minOutdoorTemp')
	def readMaxOutdoorTemperature(self)          : return self._snowmelter.readParameterValue('maxOutdoorTemp')
		
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

	def getCirculationPumpState(self):
		return self._snowmelter.getSecondaryPumpState().getValue()
	
	def circulationPumpIsOn (self): return self.getCirculationPumpState() != self.RELAY_OFF
	def circulationPumpIsOff(self): return self.getCirculationPumpState() == self.RELAY_OFF
	
	def setBacwardFlowTemperature(self, value):
		t = self._snowmelter.getBackwardFlowTemperature()
		self.set_sensor_value(t, value)
		
	def run(self):
		plateSetpoint = self.readRequiredPlateTemperatureValue()
		
		if plateSetpoint is None:
			self._status = 'FAIL'
			printError('Проблема! не удалось получить уставку плиты')
			return
		
		tFrostProtect = self.readFrostProtectionTemperatureValue()
		
		if tFrostProtect is None:
			self._status = 'FAIL'
			printError('Test fail! Can\'t get frost protect temp')
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
		
		printLog('Warm up')
		self.wait(30)
		
		printLog('Waiting for circulation pump to switch on')
		if self.wait_event(self.circulationPumpIsOn, 60):
			printLog('ok, cirulation pump is working')
		else:
			self._status = 'FAIL'
			printError('Test fail! Pump don\'t work')
			return
			
		self.wait(2)
		
		printLog('making "cold" backward flow temperature')
		self.setBacwardFlowTemperature(tFrostProtect - 1)
		
		pumpSwitchOffDuration = 5*60
		pumpSwitchOffTimeout  = 2*60
		
		printLog(f'Waiting for circulation pump to switch off for at least {pumpSwitchOffDuration} seconds')
		
		if self.wait_state_permanence(self.circulationPumpIsOff, pumpSwitchOffDuration, pumpSwitchOffTimeout):
			printLog('Test Ok!')
			self._status = 'OK'
		else:
			printError('Test fail! Pump don\'t switch off')
			self._status = 'FAIL'
		


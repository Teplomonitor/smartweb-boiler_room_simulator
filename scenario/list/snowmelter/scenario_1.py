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

	def readFrostProtectionTemperatureValue(self): return self._snowmelter.read_parameter_value('frostProtectionTemp')
	def readRequiredPlateTemperatureValue(self)  : return self._snowmelter.read_parameter_value('reqPlateTemp')
	def readMinOutdoorTemperature(self)          : return self._snowmelter.read_parameter_value('minOutdoorTemp')
	def readMaxOutdoorTemperature(self)          : return self._snowmelter.read_parameter_value('maxOutdoorTemp')
		
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
		return self._snowmelter.getSecondaryPumpState().get_value()
	
	def circulationPumpIsOn (self): return self.getCirculationPumpState() != self.RELAY_OFF
	def circulationPumpIsOff(self): return self.getCirculationPumpState() == self.RELAY_OFF
	
	def setBacwardFlowTemperature(self, value):
		t = self._snowmelter.getBackwardFlowTemperature()
		self.set_sensor_value(t, value)
		
	def run(self):
		plateSetpoint = self.readRequiredPlateTemperatureValue()
		
		if plateSetpoint is None:
			self._status = 'FAIL'
			print_error('Проблема! не удалось получить уставку плиты')
			return
		
		tFrostProtect = self.readFrostProtectionTemperatureValue()
		
		if tFrostProtect is None:
			self._status = 'FAIL'
			print_error('Test fail! Can\'t get frost protect temp')
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
		
		print_log('Warm up')
		self.wait(30)
		
		print_log('Waiting for circulation pump to switch on')
		if self.wait_event(self.circulationPumpIsOn, 60):
			print_log('ok, cirulation pump is working')
		else:
			self._status = 'FAIL'
			print_error('Test fail! Pump don\'t work')
			return
			
		self.wait(2)
		
		print_log('making "cold" backward flow temperature')
		self.setBacwardFlowTemperature(tFrostProtect - 1)
		
		pumpSwitchOffDuration = 5*60
		pumpSwitchOffTimeout  = 2*60
		
		print_log(f'Waiting for circulation pump to switch off for at least {pumpSwitchOffDuration} seconds')
		
		if self.wait_state_permanence(self.circulationPumpIsOff, pumpSwitchOffDuration, pumpSwitchOffTimeout):
			print_log('Test Ok!')
			self._status = 'OK'
		else:
			print_error('Test fail! Pump don\'t switch off')
			self._status = 'FAIL'
		


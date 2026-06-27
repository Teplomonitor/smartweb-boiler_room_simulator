'''
@author: admin
'''

from consoleLog import printLog   as printLog
from consoleLog import printError as printError
from scenario.scenario import Scenario as Parent

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._snowmelter = self._programList['snowmelter']
		self._outdoor    = self._programList['oat']
		
	def get_scenario_title(self):
		return 'scenario 4'
	
	def get_scenario_description(self):
		return 'проверить, что насос загрузки поддерживает заданную температуру на выходе из теплообменника'
	
	def get_checklist_id(self):
		return '3.9.4'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'snowmelter': 'SNOWMELT',
			'oat'       : 'OUTDOOR_SENSOR',
		}
		return requiredProgramTypesList
	
	def get_default_preset(self):
		return 'snowmelter'
		
	def getSourceTemperature(self):
		return self._sim._collector.getDirectTemperature()

		
	def readRequiredPlateTemperatureValue(self): return self._snowmelter.read_parameter_value('reqPlateTemp')
	def readMinOutdoorTemperature(self)        : return self._snowmelter.read_parameter_value('minOutdoorTemp')
	def readMaxOutdoorTemperature(self)        : return self._snowmelter.read_parameter_value('maxOutdoorTemp')
	def readSnowmelterOutdoorTemperature(self) : return self._snowmelter.read_parameter_value('outdoorTemp')
	def readRequiredFlowTemperature(self)      : return self._snowmelter.read_parameter_value('reqFlowTemp')
	
	def getDirectFlowTemperature(self): return self._snowmelter.getDirectFlowTemperature().getValue()
	
	def getCirculationPumpState(self):
		return self._snowmelter.getSecondaryPumpState().getValue()
	
	def getLoadingPumpState(self):
		return self._snowmelter.getPrimaryPumpState().getValue()
	
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
		
		def outdoorTemperatureIsOk():
			oat = self.readSnowmelterOutdoorTemperature()
			return oat > minTemp and oat < maxTemp
		
		return self.wait_event(self.outdoorTemperatureIsOk, 5*60, eventCheckPeriod = 5)

	def getAverageValue(self, array, period):
		pass
	
	def checkFlowTemperatureControl(self):
		tReq = self.readRequiredFlowTemperature()
		
		def getRequiredValue():
			return tReq
		
		flowControlDuration = 10*60
		maxCheckDuration    = 30*60
		
		result = self.wait_value_maintaining(
			self.getDirectFlowTemperature,
			getRequiredValue,
			flowControlDuration,
			maxCheckDuration,
			supplyValueHandler = self.getSourceTemperature
			)
		
		return result
	
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
		
		
		printLog('проверяем, что температура держится в пределах заданного значения')
		result = self.checkFlowTemperatureControl()
		
		if result:
			self._status = 'OK'
		else:
			self._status = 'FAIL'


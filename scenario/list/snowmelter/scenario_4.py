'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.snowmelter import SnowmelterScenario as Parent

class Scenario(Parent):
	def get_scenario_title(self):
		return 'scenario 4'
	
	def get_scenario_description(self):
		return 'проверить, что насос загрузки поддерживает заданную температуру на выходе из теплообменника'
	
	def get_checklist_id(self):
		return '3.9.4'
	
	def getSourceTemperature(self):
		return self._sim._collector.get_direct_temperature()

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

	def setMediumOutdoorTemperature(self):
		# override parent to wait until outdoor sensor reads inside the allowed bounds
		minTemp = self.readMinOutdoorTemperature()
		maxTemp = self.readMaxOutdoorTemperature()

		if (minTemp is None) or (maxTemp is None):
			return False

		midTemp = (minTemp + maxTemp)/2
		self.setOutdoorTemperature(midTemp)

		def outdoorTemperatureIsOk():
			oat = self.readSnowmelterOutdoorTemperature()
			return oat > minTemp and oat < maxTemp

		return self.wait_event(outdoorTemperatureIsOk, 5*60, eventCheckPeriod = 5)

	def run(self):
		plateSetpoint = self.readRequiredPlateTemperatureValue()
		
		if plateSetpoint is None:
			print_error('Проблема! не удалось получить уставку плиты')
			self._status = 'FAIL'
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
		
		print_log('ждём, пока система устаканится')
		self.wait(30)
		
		
		print_log('проверяем, что температура держится в пределах заданного значения')
		result = self.checkFlowTemperatureControl()
		
		if result:
			self._status = 'OK'
		else:
			self._status = 'FAIL'


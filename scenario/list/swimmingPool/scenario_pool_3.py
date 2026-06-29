'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.scenario import Scenario   as Parent

class Scenario(Parent):
	
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._pool   = self._programList['pool']

	def get_scenario_title(self): return 'pool test 3'
	
	def get_scenario_description(self):
		return 'Программа включает выход "Подпитка" при низком уровне воды в бассейне'
	
	def get_checklist_id(self): return '3.11.3'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'pool'   : 'POOL',
		}
		return requiredProgramTypesList
	
	def get_default_preset(self): return 'swimmingPool'

	def getWaterLevelControlState(self): return self._pool.get_output_channel('waterLevelControl').get_value()
	
	def waterLevelControlIsOn (self): return self.getWaterLevelControlState() != self.RELAY_OFF
	def waterLevelControlIsOff(self): return not self.waterLevelControlIsOn()
	
	def setWaterLevel(self, value):
		waterLevel = self._pool.get_input_channel('waterLevel')
		self.set_sensor_value(waterLevel, value)
	
	def run(self):
		print_log('Убедимся, что программа бассейна активна')
		self.wait(1)
		
		# Устанавливаем нормальный уровень воды (SENSOR_SHORT_VALUE = 'short')
		# В этом состоянии выход подпитки должен быть отключен
		SENSOR_SHORT_VALUE = 'short'
		print_log(f'устанавливаем нормальный уровень воды (значение {SENSOR_SHORT_VALUE})')
		self.setWaterLevel(SENSOR_SHORT_VALUE)
		self.wait(2)
		
		print_log('проверяем, что выход "Подпитка" выключен при нормальном уровне воды')
		if not self.waterLevelControlIsOff():
			self._status = 'FAIL'
			print_error('Плохо! Выход "Подпитка" должен быть выключен при нормальном уровне воды')
			return
		
		self.wait(1)
		
		# Устанавливаем низкий уровень воды (любое значение кроме SENSOR_SHORT_VALUE)
		WATER_LEVEL_LOW = 'open'
		print_log(f'устанавливаем низкий уровень воды (значение {WATER_LEVEL_LOW})')
		self.setWaterLevel(WATER_LEVEL_LOW)
		self.wait(1)
		
		print_log('ждём, что выход "Подпитка" включится при низком уровне воды')
		waterLevelControlSwitchOnTimeout = 30
		if self.wait_event(self.waterLevelControlIsOn, waterLevelControlSwitchOnTimeout):
			print_log('Хорошо, выход "Подпитка" включен')
		else:
			self._status = 'FAIL'
			print_error('Плохо, выход "Подпитка" не включается при низком уровне воды')
			return
		
		self.wait(1)
		
		# Восстанавливаем нормальный уровень воды
		print_log('восстанавливаем нормальный уровень воды')
		self.setWaterLevel(SENSOR_SHORT_VALUE)
		self.wait(1)
		
		print_log('ждём, что выход "Подпитка" выключится при восстановленном уровне воды')
		waterLevelControlSwitchOffTimeout = 30
		if self.wait_event(self.waterLevelControlIsOff, waterLevelControlSwitchOffTimeout):
			print_log('Хорошо! Выход "Подпитка" включается и выключается корректно')
			self._status = 'OK'
		else:
			self._status = 'FAIL'
			print_error('Плохо, выход "Подпитка" не выключается после восстановления уровня воды')

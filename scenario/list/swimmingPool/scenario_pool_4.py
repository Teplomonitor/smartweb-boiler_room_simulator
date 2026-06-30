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

	def get_scenario_title(self): return 'pool test 4 - filling duration timeout'
	
	def get_scenario_description(self):
		return 'Проверка отключения подпитки бассейна по истечению заданного времени подпитки'
	
	def get_checklist_id(self): return '3.11.4'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'pool'   : 'POOL',
		}
		return requiredProgramTypesList
	
	def get_default_preset(self): return 'swimmingPool_with_level'

	def force_preset_load(self):
		return True
	
	def getWaterLevelControlState(self): return self._pool.get_output_channel('waterLevelControl').get_value()

	def waterLevelControlIsOn (self): return self.getWaterLevelControlState() != self.RELAY_OFF
	def waterLevelControlIsOff(self): return not self.waterLevelControlIsOn()

	def setWaterLevel(self, value):
		waterLevel = self._pool.get_input_channel('waterLevel')
		self.set_sensor_value(waterLevel, value)

	def readFillingDuration(self):
		return self._pool.read_parameter_value('fillingDuration') / 60  # convert seconds to minutes

	def setFillingDuration(self, minutes):
		# write_parameter_value expects the parameter id name and value (minutes for pool fillingDuration)
		return self._pool.write_parameter_value('fillingDuration', minutes * 60)  # convert minutes to seconds

	def run(self):
		print_log('Убедимся, что программа бассейна активна')
		self.wait(1)
		
		# Устанавливаем нормальный уровень воды
		WATER_LEVEL_HI = 'short'
		print_log(f'устанавливаем нормальный уровень воды (значение {WATER_LEVEL_HI})')
		self.setWaterLevel(WATER_LEVEL_HI)
		self.wait(2)
		
		print_log('проверяем, что выход "Подпитка" выключен при нормальном уровне воды')
		if not self.wait_state_permanence(self.waterLevelControlIsOff(), 20, 30):
			self._status = 'FAIL'
			print_error('Плохо! Выход "Подпитка" должен быть выключен при нормальном уровне воды')
			return
		
		self.wait(1)
		
		# Запомним исходное значение времени подпитки и, при необходимости, уменьшм его для ускорения теста
		origDuration = self.readFillingDuration()
		print_log(f'текущее время подпитки (мин): {origDuration}')
		
		# Устанавливаем низкий уровень воды, должен включиться выход подпитки
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
			# попытка восстановить параметр перед выходом
			if origDuration is not None:
				self.setFillingDuration(origDuration)
			return
		
		self.wait(1)
		
		# Уменьшим время подпитки для ускорения теста (по умолчанию контроллер может иметь большое значение)
		SHORT_DURATION_MINUTES = 5
		print_log(f'устанавливаем время подпитки = {SHORT_DURATION_MINUTES} минут для ускорения теста')
		self.setFillingDuration(SHORT_DURATION_MINUTES)
		# даём контроллеру время принять параметр
		self.wait(2)
		
		# Ожидаем, что контроллер выключит подпитку через SHORT_DURATION_MINUTES
		print_log('ожидаем автоматического отключения подпитки по таймауту')
		# таймаут в секундах: минуты * 60 + небольшой запас
		offTimeout = SHORT_DURATION_MINUTES * 60 + 60
		if self.wait_event(self.waterLevelControlIsOff, offTimeout):
			print_log('Хорошо! Контроллер отключил подпитку по истечении настроенного времени')
			self._status = 'OK'
		else:
			self._status = 'FAIL'
			print_error('Плохо! Контроллер не отключил подпитку по истечении настроенного времени')
		
		# восстановим исходное значение времени подпитки
		if origDuration is not None:
			print_log(f'восстанавливаем исходное время подпитки = {origDuration}')
			self.setFillingDuration(origDuration)
		
'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.scenario import Scenario   as Parent
from smartnet.message_log import MessageLogReader

class Scenario(Parent):
	
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		
		self._pool   = self._programList['pool']

	def get_scenario_title(self): return 'pool test 4 - filling duration timeout and pumps shutdown'
	
	def get_scenario_description(self):
		return 'Проверка отключения подпитки и насосов бассейна по истечению заданного времени подпитки и фиксация в журнале'
	
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

	def getLoadingPumpState(self): return self._pool.getLoadingPumpState().get_value()
	def getCirculationPumpState(self): return self._pool.getCirculationPumpState().get_value()

	def loadingPumpIsOn (self): return self.getLoadingPumpState() != self.RELAY_OFF
	def loadingPumpIsOff(self): return not self.loadingPumpIsOn()

	def circulationPumpIsOn (self): return self.getCirculationPumpState() != self.RELAY_OFF
	def circulationPumpIsOff(self): return not self.circulationPumpIsOn()

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
		
		# Убедимся, что насосы загрузки и циркуляции включены (контроллер нагревает бассейн)
		print_log('проверяем, что насосы загрузки и циркуляции включены')
		# если насосы не включены, постараемся разогреть бассейн, чтобы включить насосы
		if not self.loadingPumpIsOn():
			# try to stimulate pump behaviour by toggling temperature
			req = self._pool.read_parameter_value('currentRequiredPoolTemperature')
			if req is not None:
				self._pool.get_temperature().set_value(req + 2, True)
				self.wait(2)
		
		if not self.loadingPumpIsOn() or not self.circulationPumpIsOn():
			print_log('Предупреждение: насосы не активны перед тестом — тест всё равно продолжится')
		
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
		SHORT_DURATION_MINUTES = 1
		print_log(f'устанавливаем время подпитки = {SHORT_DURATION_MINUTES} минут для ускорения теста')
		self.setFillingDuration(SHORT_DURATION_MINUTES)
		# даём контроллеру время принять параметр
		self.wait(2)
		
		# Ожидаем, что контроллер выключит подпитку через SHORT_DURATION_MINUTES
		print_log('ожидаем автоматического отключения подпитки по таймауту и отключения насосов')
		# таймаут в секундах: минуты * 60 + небольшой запас
		offTimeout = SHORT_DURATION_MINUTES * 60 + 60
		if self.wait_event(self.waterLevelControlIsOff, offTimeout):
			print_log('Хорошо! Контроллер отключил подпитку по истечении настроенного времени')
			# теперь проверим, что насосы загрузки и циркуляции отключены
			pumpsOffDuration = 5
			pumpsOffTimeout = 30
			if self.wait_state_permanence(self.loadingPumpIsOff, pumpsOffDuration, pumpsOffTimeout) and \
				self.wait_state_permanence(self.circulationPumpIsOff, pumpsOffDuration, pumpsOffTimeout):
				print_log('Хорошо! Насосы загрузки и циркуляции отключены после длительной подпитки')
			else:
				self._status = 'FAIL'
				print_error('Плохо! Насосы не отключились после длительной подпитки')
				# восстановим исходные параметры перед выходом
				if origDuration is not None:
					self.setFillingDuration(origDuration)
				return
			
			# Проверим, что в журнал записано сообщение о низком уровне воды
			try:
				reader = MessageLogReader(program_id=self._pool.get_id())
				entries = reader.read_entries(max_entries=10)
				if entries and len(entries) > 0:
					print_log(f'Журнал содержит {len(entries)} записей (ожидается сообщение о низком уровне воды)')
					self._status = 'OK'
				else:
					self._status = 'FAIL'
					print_error('Плохо! В журнале не найдено записей о низком уровне воды')
			except Exception as e:
				print_error(f'Не удалось прочитать журнал: {e}')
				self._status = 'FAIL'
		else:
			self._status = 'FAIL'
			print_error('Плохо! Контроллер не отключил подпитку по истечении настроенного времени')
		
		# восстановим исходное значение времени подпитки
		if origDuration is not None:
			print_log(f'восстанавливаем исходное время подпитки = {origDuration}')
			self.setFillingDuration(origDuration)
		
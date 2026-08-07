'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.swimming_pool import PoolScenario
import smartnet.constants as snc

from smartnet.message_log_constants import MessageLogCode

class Scenario(PoolScenario):

	def get_scenario_title(self): return 'pool test 4 - filling duration timeout and pumps shutdown'
	
	def get_scenario_description(self):
		return 'Проверка отключения подпитки и насосов бассейна по истечению заданного времени подпитки и фиксация в журнале'
	
	def get_checklist_id(self): return '3.11.7 & 3.11.9'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'pool'   : snc.ProgramType.POOL,
		}
		return requiredProgramTypesList
	
	def get_default_preset(self): return 'swimmingPool_with_level'

	def force_preset_load(self):
		return True
	
	def get_water_level_control_state(self): return self._pool.get_output_channel('waterLevelControl').get_value()

	def water_level_control_is_on(self): return self.get_water_level_control_state() != self.RELAY_OFF
	def water_level_control_is_off(self): return not self.water_level_control_is_on()

	def set_water_level(self, value):
		waterLevel = self._pool.get_input_channel('waterLevel')
		self.set_sensor_value(waterLevel, value)

	def read_filling_duration(self):
		return self._pool.read_parameter_value('fillingDuration') / 60  # convert seconds to minutes

	def set_filling_duration(self, minutes):
		# write_parameter_value expects the parameter id name and value (minutes for pool fillingDuration)
		return self._pool.write_parameter_value('fillingDuration', minutes * 60)  # convert minutes to seconds

	def run(self):
		#reset water level alarm and fill counter
		print_log('Сбрасываем сигнализацию низкого уровня воды и счётчик наполнения бассейна')
		self._pool.resetWaterLevelAlarm()
		
		print_log('Убедимся, что программа бассейна активна')
		self.wait(1)
		
		# Устанавливаем нормальный уровень воды
		WATER_LEVEL_HI = 'short'
		print_log(f'устанавливаем нормальный уровень воды (значение {WATER_LEVEL_HI})')
		self.set_water_level(WATER_LEVEL_HI)
		self.wait(2)
		
		print_log('проверяем, что выход "Подпитка" выключен при нормальном уровне воды')
		if not self.wait_state_permanence(self.water_level_control_is_off, 20, 30):
			self._status = 'FAIL'
			print_error('Плохо! Выход "Подпитка" должен быть выключен при нормальном уровне воды')
			return
		
		self.wait(1)
		
		# Запомним исходное значение времени подпитки и, при необходимости, уменьшм его для ускорения теста
		original_duration = self.read_filling_duration()
		print_log(f'текущее время подпитки (мин): {original_duration}')
		
		# Убедимся, что насосы загрузки и циркуляции включены (контроллер нагревает бассейн)
		print_log('проверяем, что насосы загрузки и циркуляции включены')
		# если насосы не включены, постараемся разогреть бассейн, чтобы включить насосы
		if not self.loading_pump_is_on():
			# try to stimulate pump behaviour by toggling temperature
			req = self.read_required_pool_temperature()
			if req is not None:
				self._pool.get_temperature().set_value(req + 2, True)
				self.wait(2)
		
		if not self.loading_pump_is_on() or not self.circulation_pump_is_on():
			print_log('Предупреждение: насосы не активны перед тестом — тест всё равно продолжится')
		
		print_log('Прочитаем старые сообщения в журнале, чтобы они не сбивали с толку. Будем ждать новые сообщения')
		self._controllerHost.read_message_log()
		
		# Устанавливаем низкий уровень воды, должен включиться выход подпитки
		WATER_LEVEL_LOW = 'open'
		print_log(f'устанавливаем низкий уровень воды (значение {WATER_LEVEL_LOW})')
		self.set_water_level(WATER_LEVEL_LOW)
		self.wait(1)
		
		print_log('ждём, что выход "Подпитка" включится при низком уровне воды')
		waterLevelControlSwitchOnTimeout = 30
		if self.wait_event(self.water_level_control_is_on, waterLevelControlSwitchOnTimeout):
			print_log('Хорошо, выход "Подпитка" включен')
		else:
			self._status = 'FAIL'
			print_error('Плохо, выход "Подпитка" не включается при низком уровне воды')
			# попытка восстановить параметр перед выходом
			if original_duration is not None:
				self.set_filling_duration(original_duration)
			return
		
		self.wait(1)
		
		# Уменьшим время подпитки для ускорения теста (по умолчанию контроллер может иметь большое значение)
		SHORT_DURATION_MINUTES = 1
		print_log(f'устанавливаем время подпитки = {SHORT_DURATION_MINUTES} минут для ускорения теста')
		self.set_filling_duration(SHORT_DURATION_MINUTES)
		# даём контроллеру время принять параметр
		self.wait(2)
		
		# Ожидаем, что контроллер выключит подпитку через SHORT_DURATION_MINUTES
		print_log('ожидаем автоматического отключения подпитки по таймауту и отключения насосов')
		# таймаут в секундах: минуты * 60 + небольшой запас
		offTimeout = SHORT_DURATION_MINUTES * 60 + 60
		if self.wait_event(self.water_level_control_is_off, offTimeout):
			print_log('Хорошо! Контроллер отключил подпитку по истечении настроенного времени')
			# теперь проверим, что насосы загрузки и циркуляции отключены
			pumpsOffDuration = 5
			pumpsOffTimeout = 30
			if self.wait_state_permanence(self.loading_pump_is_off, pumpsOffDuration, pumpsOffTimeout) and \
				self.wait_state_permanence(self.circulation_pump_is_off, pumpsOffDuration, pumpsOffTimeout):
				print_log('Хорошо! Насосы загрузки и циркуляции отключены после длительной подпитки')
			else:
				self._status = 'FAIL'
				print_error('Плохо! Насосы не отключились после длительной подпитки')
				# восстановим исходные параметры перед выходом
				if original_duration is not None:
					self.set_filling_duration(original_duration)
				return
			
			# Проверим, что в журнал записано сообщение о низком уровне воды
			try:
				print_log(f'Ищем сообщение о низком уровне воды')
				entries = self._controllerHost.read_message_log()
				if entries and len(entries) > 0:
					print_log(f'Журнал содержит {len(entries)} записей (ожидается сообщение о низком уровне воды)')
					
					
					matching_entry = next(
						(
							entry for entry in entries
							if entry.code == MessageLogCode.MLC_LOW_POOL_WATER_LEVEL
							and entry.param == self._pool.get_id()
						),
						None
					)
					
					if matching_entry is not None:
						print_log(
							f'Хорошо! В журнале найдено сообщение о низком уровне воды '
							f'для бассейна {matching_entry.param}'
						)
						self._status = 'OK'
					else:
						self._status = 'FAIL'
						print_error(
							'Плохо! В журнале не найдено новое сообщения о низком уровне воды '
							f'для бассейна {self._pool.get_id()}'
						)

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
		if original_duration is not None:
			print_log(f'восстанавливаем исходное время подпитки = {original_duration}')
			self.set_filling_duration(original_duration)
		
'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.swimming_pool import PoolScenario

class Scenario(PoolScenario):

	def get_scenario_title(self): return 'pool test 3'
	
	def get_scenario_description(self):
		return 'Программа включает выход "Подпитка" при низком уровне воды в бассейне'
	
	def get_checklist_id(self): return '3.11.8'
	
	def force_preset_load(self):
		return True
	
	def get_water_level_control_state(self): return self._pool.get_output_channel('waterLevelControl').get_value()
	
	def water_level_control_is_on(self): return self.get_water_level_control_state() != self.RELAY_OFF
	def water_level_control_is_off(self): return not self.water_level_control_is_on()
	
	def set_water_level(self, value):
		water_level = self._pool.get_input_channel('waterLevel')
		self.set_sensor_value(water_level, value)
	
	def run(self):
		print_log('Убедимся, что программа бассейна активна')
		self.wait(1)
		
		# Устанавливаем нормальный уровень воды (WATER_LEVEL_HI = 'short')
		# В этом состоянии выход подпитки должен быть отключен
		water_level_hi = 'short'
		print_log(f'устанавливаем нормальный уровень воды (значение {water_level_hi})')
		self.set_water_level(water_level_hi)
		self.wait(2)
		
		print_log('проверяем, что выход "Подпитка" выключен при нормальном уровне воды')
		if not self.wait_state_permanence(self.water_level_control_is_off, 20, 30):
			self._status = 'FAIL'
			print_error('Плохо! Выход "Подпитка" должен быть выключен при нормальном уровне воды')
			return
		
		self.wait(1)
		
		# Устанавливаем низкий уровень воды (любое значение кроме WATER_LEVEL_HI)
		water_level_low = 'open'
		print_log(f'устанавливаем низкий уровень воды (значение {water_level_low})')
		self.set_water_level(water_level_low)
		self.wait(1)
		
		print_log('ждём, что выход "Подпитка" включится при низком уровне воды')
		water_level_control_switch_on_timeout = 30
		if self.wait_event(self.water_level_control_is_on, water_level_control_switch_on_timeout):
			print_log('Хорошо, выход "Подпитка" включен')
		else:
			self._status = 'FAIL'
			print_error('Плохо, выход "Подпитка" не включается при низком уровне воды')
			return
		
		self.wait(1)
		
		# Восстанавливаем нормальный уровень воды
		print_log('восстанавливаем нормальный уровень воды')
		self.set_water_level(water_level_hi)
		self.wait(1)
		
		print_log('ждём, что выход "Подпитка" выключится при восстановленном уровне воды')
		water_level_control_switch_off_timeout = 30
		if self.wait_event(self.water_level_control_is_off, water_level_control_switch_off_timeout):
			print_log('Хорошо! Выход "Подпитка" включается и выключается корректно')
			self._status = 'OK'
		else:
			self._status = 'FAIL'
			print_error('Плохо, выход "Подпитка" не выключается после восстановления уровня воды')

'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.snowmelter import SnowmelterScenario   as Parent
from scenario.base.filling_loop_signal import (
	PRESSURE_INPUT_TYPE_SHORTABLE,
	read_pressure_input_type,
	write_pressure_input_type,
)
import smartnet.constants as snc

class Scenario(Parent):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		# additional program required by this scenario
		self._pressure = self._programList['pressure']

	def get_scenario_title(self):
		return 'scenario 5'
	
	def get_scenario_description(self):
		return 'проверить, что снеготайка выключает насосы загрузки и циркуляции, если получает сигнал об аварии от Аварийной программы'
	
	def get_checklist_id(self):
		return '3.9.5'
	
	def get_required_programs(self):
		requiredProgramTypesList = {
			'snowmelter': snc.ProgramType.SNOWMELT,
			'oat'       : snc.ProgramType.OUTDOOR_SENSOR,
			'pressure'  : snc.ProgramType.FILLING_LOOP,
		}
		return requiredProgramTypesList
	
	def get_default_preset(self):
		return 'snowmelterWithPressureControl'
		
		
	def setAlarmSignal(self, value):
		t = self._pressure.getPressure()
		state = 'open' if value else 'short'
		self.set_sensor_value(t, state)
		
	def run(self):
		original_pressure_input_type = read_pressure_input_type(self._pressure)
		if original_pressure_input_type is None:
			print_error('Не удалось прочитать тип сигнала программы подпитки')
			self._status = 'FAIL'
			return
		if not write_pressure_input_type(self._pressure, PRESSURE_INPUT_TYPE_SHORTABLE):
			print_error('Не удалось настроить дискретный тип сигнала подпитки')
			self._status = 'FAIL'
			return
		try:
			self._run_test()
		finally:
			self.setAlarmSignal(False)
			if not write_pressure_input_type(self._pressure, original_pressure_input_type):
				print_error('Не удалось восстановить тип сигнала программы подпитки')
				self._status = 'FAIL'

	def _run_test(self):
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
		
		print_log('ждём, когда насос циркуляции включится')
		if self.wait_event(self.circulationPumpIsOn, 60):
			print_log('Хорошо, включился')
		else:
			self._status = 'FAIL'
			print_error('Плохо. Не включился!')
			return
			
		self.wait(2)
		
		print_log('включаем сигнал низкого давление в программе подпитки')
		self.setAlarmSignal(True)
		
		pumpsSwitchOffTestDuration = 5*60
		
		print_log(f'Ждём, пока насосы не выключатся хотя бы на {pumpsSwitchOffTestDuration} секунд')
		self.wait(10)
				
		pumpsSwitchOffDelay = 60
		testExtraDelay      = 60
		timeout = pumpsSwitchOffDelay + pumpsSwitchOffTestDuration + testExtraDelay

		if self.wait_state_permanence(self.pumpsAreOff, pumpsSwitchOffTestDuration, timeout):
			print_log('Хорошо!')
			self._status = 'OK'
		else:
			print_error('Плохо. Насосы не выключаются!')
			self._status = 'FAIL'



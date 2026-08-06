'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.swimming_pool import PoolScenario
import smartnet.constants as snc


class Scenario(PoolScenario):
	def __init__(self, controllerHost, sim):
		super().__init__(controllerHost, sim)
		self._pressure = self._programList['pressure']

	def get_scenario_title(self): return 'pool test 6 - pumps shutdown on alarm'

	def get_scenario_description(self):
		return 'Бассейн выключает насосы загрузки и циркуляции при аварийном сигнале от Аварийной программы'

	def get_checklist_id(self): return '3.11.6'

	def get_required_programs(self):
		return {
			'pool': snc.ProgramType.POOL,
			'pressure': snc.ProgramType.FILLING_LOOP,
		}

	def get_default_preset(self): return 'swimmingPoolWithPressureControl'

	def pumps_are_on(self):
		return self.loading_pump_is_on() and self.circulation_pump_is_on()

	def pumps_are_off(self):
		return self.loading_pump_is_off() and self.circulation_pump_is_off()

	def set_alarm_signal(self, value):
		pressure = self._pressure.getPressure()
		state = 'open' if value else 'short'
		self.set_sensor_value(pressure, state)

	def run(self):
		pool_setpoint = self.read_required_pool_temperature()
		if pool_setpoint is None:
			self._status = 'FAIL'
			print_error('Проблема! не удалось получить уставку бассейна')
			return

		try:
			print_log('снимаем аварийный сигнал программы подпитки')
			self.set_alarm_signal(False)

			print_log('делаем воду в бассейне холодной для включения насосов')
			self.set_pool_temperature(pool_setpoint - 1.5)
			self.wait(2)

			print_log('ждём включения насосов загрузки и циркуляции')
			if not self.wait_event(self.pumps_are_on, 60):
				self._status = 'FAIL'
				print_error('Плохо, насосы загрузки и циркуляции не включились')
				return

			print_log('Хорошо, оба насоса работают')
			self.wait(1)

			print_log('подаём аварийный сигнал от Аварийной программы')
			self.set_alarm_signal(True)
			self.wait(2)

			pumps_off_duration = 5
			pumps_off_timeout = 60
			print_log('ждём устойчивого отключения насосов загрузки и циркуляции')
			if self.wait_state_permanence(
				self.pumps_are_off,
				pumps_off_duration,
				pumps_off_timeout,
			):
				print_log('Хорошо! Оба насоса отключились по аварийному сигналу')
				self._status = 'OK'
			else:
				self._status = 'FAIL'
				print_error('Плохо! Насосы не отключились по аварийному сигналу')
		finally:
			print_log('сбрасываем аварийный сигнал программы подпитки')
			self.set_alarm_signal(False)

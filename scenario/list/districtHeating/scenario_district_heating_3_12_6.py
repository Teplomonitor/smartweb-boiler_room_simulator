from consoleLog import print_error
from consoleLog import print_log
from scenario.base.district_heating import DistrictHeatingScenario
import smartnet.constants as snc
import smartnet.remoteControl as sr


class Scenario(DistrictHeatingScenario):
	STABILIZATION_DURATION = 60
	FLOW_CONTROL_DURATION = 10 * 60
	FLOW_CONTROL_TIMEOUT = 30 * 60
	MAXIMUM_TEMPERATURE_ERROR = 3

	def get_scenario_title(self):
		return 'District Heating: supplied temperature follows current setpoint'

	def get_scenario_description(self):
		return (
			'ИТП удерживает текущую требуемую температуру подачи в дом с расхождением '
			'не более 3 градусов в среднем за 10 минут'
		)

	def get_checklist_id(self):
		return '3.12.6'

	def get_default_preset(self):
		return 'district_heating_3_12_6'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'outdoor': snc.ProgramType.OUTDOOR_SENSOR,
			'heatingCircuit': snc.ProgramType.HEATING_CIRCUIT,
		}

	def read_required_temperature(self):
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.TEMPERATURE_SOURCE,
			parameterId=snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE,
			programId=self._district_heating.get_id(),
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def run(self):
		direct_temperature = self._district_heating.get_input_channel('direct_temp')

		if not direct_temperature.is_mapped():
			print_error('Не найден датчик подачи в дом ИТП')
			self._status = 'FAIL'
			return

		# Set outdoor temperature to 0 degrees to ensure that the heating system is active and the flow temperature is being controlled.
		# also we don't need very cold outdoor temperature to test flow temperature control,
		# becase District heating may fail to maintain flow temperature if outdoor temperature is too low.
		
		
		print_log(
			f'Делаем на улице 0 градусов, чтобы ИТП работал и контролировал температуру подачи в дом'
		)
		self.set_outdoor_temperature(0)
		
		if not self.wait(10):
			self._status = 'FAIL'
			return
		
		print_log(
			f'Ждём {self.STABILIZATION_DURATION} секунд перед чтением текущей уставки ИТП'
		)
		if not self.wait(self.STABILIZATION_DURATION):
			self._status = 'FAIL'
			return

		required_temperature = self.read_required_temperature()
		if required_temperature is None:
			print_error('Не удалось получить текущую уставку температуры подачи ИТП')
			self._status = 'FAIL'
			return

		print_log(
			f'Текущая уставка температуры подачи в дом: '
			f'{required_temperature:.1f} C'
		)
		print_log(
			f'Проверяем поддержание температуры подачи в дом в течение '
			f'{self.FLOW_CONTROL_DURATION} секунд'
		)
		result = self.wait_value_maintaining(
			direct_temperature.get_value,
			self.read_required_temperature,
			self.FLOW_CONTROL_DURATION,
			self.FLOW_CONTROL_TIMEOUT,
			dtAvrMax=self.MAXIMUM_TEMPERATURE_ERROR,
		)
		if result:
			self._status = 'OK'
		else:
			self._status = 'FAIL'
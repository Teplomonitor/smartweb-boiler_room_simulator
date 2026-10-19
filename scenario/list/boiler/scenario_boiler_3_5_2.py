from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
import smartnet.remoteControl as sr


class Scenario(Parent):
	DHW_TEST_SETPOINTS = (40, 50)
	DHW_TEST_TEMPERATURE = 20
	BOILER_HOT_TEMPERATURE = 80
	TEMPERATURE_TOLERANCE = 0.2
	REQUIRED_TEMPERATURE_TIMEOUT = 90
	BURNER_STATE_TIMEOUT = 60

	def get_scenario_title(self):
		return 'Boiler: first stage follows DHW heat demand'

	def get_scenario_description(self):
		return (
			'Первая ступень котла включается и выключается по текущей и требуемой '
			'температуре, запрошенной программой ГВС'
		)

	def get_checklist_id(self):
		return '3.5.2'

	def get_required_programs(self):
		return {
			'dhw': snc.ProgramType.DHW,
			'boiler': snc.ProgramType.BOILER,
		}

	def get_default_preset(self):
		return 'boiler_3_5_2'

	def force_preset_load(self):
		return True

	def read_boiler_required_temperature(self):
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.TEMPERATURE_SOURCE,
			parameterId=snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE,
			programId=self._boiler.get_id(),
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def read_dhw_temperature_compensation(self):
		parameter = sr.RemoteControlParameter(
			programType=snc.ProgramType.CONSUMER,
			parameterId=snc.ConsumerParameterId.TEMPERATURE_COMPENSATION,
			programId=self._dhw.get_id(),
		)
		if not parameter.read():
			return None
		return parameter.get_value()

	def boiler_required_temperature_is(self, expected):
		actual = self.read_boiler_required_temperature()
		return actual is not None and abs(actual - expected) <= self.TEMPERATURE_TOLERANCE

	def run(self):
		self._dhw = self._programList['dhw']
		self._boiler = self._programList['boiler']

		dhw_temperature = self._dhw.get_temperature()
		boiler_temperature = self._boiler.get_input_channel('temperature')
		burner_stage_1 = self._boiler.get_stage_1()

		for channel, description in (
			(dhw_temperature, 'датчик температуры ГВС'),
			(boiler_temperature, 'датчик температуры котла'),
			(burner_stage_1, 'выход первой ступени котла'),
		):
			if not channel.is_mapped():
				print_error(f'Не найден {description}')
				self._status = 'FAIL'
				return

		initial_dhw_temperature = dhw_temperature.get_value()
		initial_boiler_temperature = boiler_temperature.get_value()
		initial_work_mode = self._dhw.read_parameter_value('workMode')
		initial_comfort_temperature = self._dhw.read_parameter_value('temperatureComfort')
		temperature_compensation = self.read_dhw_temperature_compensation()

		if None in (
			initial_dhw_temperature,
			initial_boiler_temperature,
			initial_work_mode,
			initial_comfort_temperature,
			temperature_compensation,
		):
			print_error('Не удалось прочитать исходные температуры и параметры ГВС')
			self._status = 'FAIL'
			return

		try:
			print_log('Включаем комфортный режим ГВС и задаём низкую температуру бойлера ГВС')
			self._dhw.write_parameter_value('workMode', 0)
			self.set_sensor_value(dhw_temperature, self.DHW_TEST_TEMPERATURE)

			for dhw_setpoint in self.DHW_TEST_SETPOINTS:
				print_log(f'Устанавливаем требуемую температуру ГВС {dhw_setpoint} °C')
				self._dhw.write_parameter_value('temperatureComfort', dhw_setpoint)

				expected_boiler_temperature = dhw_setpoint + temperature_compensation
				print_log(
					f'Ждём запрос котлу {expected_boiler_temperature:.1f} °C '
					f'не более {self.REQUIRED_TEMPERATURE_TIMEOUT} секунд'
				)
				if not self.wait_event(
					lambda: self.boiler_required_temperature_is(expected_boiler_temperature),
					self.REQUIRED_TEMPERATURE_TIMEOUT,
				):
					actual = self.read_boiler_required_temperature()
					print_error(
						f'Котёл не получил требуемую температуру от ГВС '
						f'(ожидалось {expected_boiler_temperature:.1f} °C, получено {actual})'
					)
					self._status = 'FAIL'
					return

				print_log('Понижаем температуру котла ниже запроса ГВС')
				self.set_sensor_value(
					boiler_temperature,
					expected_boiler_temperature - 10,
				)
				if not self.wait_event(
					lambda: (
						burner_stage_1.get_value() is not None
						and burner_stage_1.get_value() != self.RELAY_OFF
					),
					self.BURNER_STATE_TIMEOUT,
				):
					print_error('Первая ступень котла не включилась при температуре ниже уставки')
					self._status = 'FAIL'
					return

				print_log('Повышаем температуру котла выше запроса ГВС')
				self.set_sensor_value(boiler_temperature, self.BOILER_HOT_TEMPERATURE)
				if not self.wait_event(
					lambda: (
						burner_stage_1.get_value() is not None
						and burner_stage_1.get_value() == self.RELAY_OFF
					),
					self.BURNER_STATE_TIMEOUT,
				):
					print_error('Первая ступень котла не выключилась при температуре выше уставки')
					self._status = 'FAIL'
					return

			print_log('Первая ступень котла реагирует на запросы ГВС и температуру котла')
			self._status = 'OK'
		finally:
			self._dhw.write_parameter_value('temperatureComfort', initial_comfort_temperature)
			self._dhw.write_parameter_value('workMode', initial_work_mode)
			self.set_sensor_value(dhw_temperature, initial_dhw_temperature)
			self.set_sensor_value(boiler_temperature, initial_boiler_temperature)

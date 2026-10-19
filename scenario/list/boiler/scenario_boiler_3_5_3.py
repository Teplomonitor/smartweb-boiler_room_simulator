from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc


class Scenario(Parent):
	PUMP_OFF_DELAY = 60 * 1000
	PUMP_OFF_MARGIN = 5
	PUMP_OFF_CONFIRMATION_TIMEOUT = 5
	BOILER_COLD_TEMPERATURE = 20
	BOILER_HOT_TEMPERATURE = 80
	BURNER_STATE_TIMEOUT = 60

	def get_scenario_title(self):
		return 'Boiler: pump switches on with stage 1 and turns off after delay'

	def get_scenario_description(self):
		return (
			'Насос котла включается вместе с первой ступенью и выключается '
			'с задержкой, заданной параметром PUMP_OFF_DELAY'
		)

	def get_checklist_id(self):
		return '3.5.3'

	def get_required_programs(self):
		return {
			'boiler': snc.ProgramType.BOILER,
		}

	def get_default_preset(self):
		return 'boiler_3_5_2'

	def force_preset_load(self):
		return True

	def run(self):
		self._boiler = self._programList['boiler']
		boiler_temperature = self._boiler.get_input_channel('temperature')
		pump = self._boiler.get_pump()
		burner_stage_1 = self._boiler.get_stage_1()

		for channel, description in (
			(boiler_temperature, 'датчик температуры котла'),
			(pump, 'насос котла'),
			(burner_stage_1, 'выход первой ступени котла'),
		):
			if not channel.is_mapped():
				print_error(f'Не найден {description}')
				self._status = 'FAIL'
				return

		initial_boiler_temperature = boiler_temperature.get_value()
		initial_pump_off_delay = self._boiler.get_pump_off_delay()

		if initial_boiler_temperature is None or initial_pump_off_delay is None:
			print_error('Не удалось прочитать исходную температуру котла или задержку насоса')
			self._status = 'FAIL'
			return

		try:
			print_log(f'Устанавливаем задержку выключения насоса {self.PUMP_OFF_DELAY} мс')
			self._boiler.set_pump_off_delay(self.PUMP_OFF_DELAY)

			print_log('Делаем котёл холодным, чтобы включилась первая ступень')
			self.set_sensor_value(boiler_temperature, self.BOILER_COLD_TEMPERATURE)

			if not self.wait_event(
				lambda: (
					burner_stage_1.get_value() is not None
					and burner_stage_1.get_value() != self.RELAY_OFF
				),
				self.BURNER_STATE_TIMEOUT,
			):
				print_error('Первая ступень котла не включилась')
				self._status = 'FAIL'
				return

			if not self.wait_event(
				lambda: (
					pump.get_value() is not None
					and pump.get_value() != self.RELAY_OFF
				),
				self.BURNER_STATE_TIMEOUT,
			):
				print_error('Насос котла не включился вместе с первой ступенью')
				self._status = 'FAIL'
				return

			print_log('Проверяем, что насос включён вместе с первой ступенью')
			if not self.wait_state_permanence(
				lambda: (
					burner_stage_1.get_value() == self.RELAY_ON
					and pump.get_value() == self.RELAY_ON
				),
				5,
				self.BURNER_STATE_TIMEOUT,
			):
				print_error('Насос котла не удерживается включённым вместе с первой ступенью')
				self._status = 'FAIL'
				return

			print_log('Повышаем температуру котла, чтобы выключить первую ступень')
			self.set_sensor_value(boiler_temperature, self.BOILER_HOT_TEMPERATURE)

			if not self.wait_event(
				lambda: (
					burner_stage_1.get_value() is not None
					and burner_stage_1.get_value() == self.RELAY_OFF
				),
				self.BURNER_STATE_TIMEOUT,
			):
				print_error('Первая ступень котла не выключилась после нагрева')
				self._status = 'FAIL'
				return

			pump_delay_seconds = self.PUMP_OFF_DELAY / 1000.0
			pump_delay_timeout = pump_delay_seconds + self.PUMP_OFF_CONFIRMATION_TIMEOUT

			print_log(
				f'Проверяем, что насос остаётся включённым '
				f'не менее {max(0, pump_delay_seconds - self.PUMP_OFF_MARGIN):.0f} секунд '
				f'до отключения по задержке'
			)
			if not self.wait_state_permanence(
				lambda: pump.get_value() == self.RELAY_ON,
				max(0, pump_delay_seconds - self.PUMP_OFF_MARGIN),
				pump_delay_timeout,
			):
				print_error(
					f'Насос выключился раньше задержки {self.PUMP_OFF_DELAY} мс '
					f'или не удержался включённым'
				)
				self._status = 'FAIL'
				return

			print_log(
				f'Ждём выключения насоса после задержки {self.PUMP_OFF_DELAY} мс '
				f'не более {pump_delay_timeout:.0f} секунд'
			)
			if not self.wait_event(
				lambda: pump.get_value() == self.RELAY_OFF,
				pump_delay_timeout,
			):
				print_error(
					f'Насос не выключился после задержки {self.PUMP_OFF_DELAY} мс '
					f'в течение {pump_delay_timeout:.0f} секунд'
				)
				self._status = 'FAIL'
				return

			print_log('Проверка задержки выключения насоса прошла успешно')
			self._status = 'OK'
		finally:
			self._boiler.set_pump_off_delay(initial_pump_off_delay)
			self.set_sensor_value(boiler_temperature, initial_boiler_temperature)

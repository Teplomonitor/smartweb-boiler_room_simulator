from consoleLog import print_error, print_log
from scenario.base.filling_loop_alarm import FillingLoopAlarmScenario
import smartnet.constants as snc


class Scenario(FillingLoopAlarmScenario):
	COLD_TEMPERATURE = 20
	DHW_COMFORT_TEMPERATURE = 60
	DHW_MODE_COMFORT = 0
	STATE_TIMEOUT = 90
	RESTART_TIMEOUT = 180
	HOLD_DURATION = 5

	def get_scenario_title(self):
		return 'Boiler: shutdown on filling loop alarm and automatic recovery'

	def get_scenario_description(self):
		return (
			'Котёл выключает горелку и насос при аварии подпитки и возобновляет '
			'нагрев после нормализации давления при сохраняющемся запросе ГВС'
		)

	def get_checklist_id(self):
		return '3.5.6'

	def get_required_programs(self):
		return {
			'dhw': snc.ProgramType.DHW,
			'boiler': snc.ProgramType.BOILER,
			'filling_loop': snc.ProgramType.FILLING_LOOP,
		}

	def get_default_preset(self):
		return 'boiler_3_5_6'

	def _heat_is_requested(self):
		value = self._read_parameter(
			self._programList['dhw'], snc.ProgramType.CONSUMER,
			snc.ConsumerParameterId.REQUIRED_TEMPERATURE,
		)
		return value is not None and value > self.COLD_TEMPERATURE

	def _boiler_is(self, heating):
		stage_1, stage_2, pump = [channel.get_value() for channel in self._boiler_outputs]
		if heating:
			return stage_1 is not None and stage_1 != self.RELAY_OFF and pump == self.RELAY_ON
		return stage_1 == self.RELAY_OFF and stage_2 == self.RELAY_OFF and pump == self.RELAY_OFF

	def _check_state(self, alarm, heating, timeout, description):
		print_log(description)
		if not self.wait_state_permanence(
			lambda: self._alarm_is(alarm) and self._heat_is_requested() and self._boiler_is(heating),
			self.HOLD_DURATION,
			timeout,
		):
			print_error(f'Не подтверждено состояние: {description}')
			return False
		return True

	def _sequence(self):
		if not self._check_state(False, True, self.RESTART_TIMEOUT, 'Нормальное давление: котёл греет по запросу ГВС'):
			return False
		self._set_pressure(self.PRESSURE_LOW)
		if not self._check_state(True, False, self.STATE_TIMEOUT, 'Низкое давление: авария подпитки выключает котёл'):
			return False
		self._set_pressure(self.PRESSURE_NORMAL)
		return self._check_state(False, True, self.RESTART_TIMEOUT, 'Давление восстановлено: котёл снова греет')

	def run(self):
		boiler = self._programList['boiler']
		dhw = self._programList['dhw']
		self._boiler_outputs = [
			boiler.get_stage_1(), boiler.get_output_channel('burner2'), boiler.get_pump(),
		]
		settings = [
			(dhw, snc.ProgramType.DHW, snc.DhwParameterId.WORK_MODE, self.DHW_MODE_COMFORT),
			(dhw, snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT, self.DHW_COMFORT_TEMPERATURE),
			(boiler, snc.ProgramType.TEMPERATURE_GENERATOR, snc.TemperatureGeneratorParameterId.MIN_OFF_TIME, 0),
		]
		sensors = [
			(boiler.get_input_channel('temperature'), self.COLD_TEMPERATURE),
			(dhw.get_temperature(), self.COLD_TEMPERATURE),
		]
		self._run_alarm_test(settings, sensors, self._boiler_outputs, self._sequence)
		if self._status == 'OK':
			print_log('Котёл отключился по аварии и восстановил работу после нормализации давления')
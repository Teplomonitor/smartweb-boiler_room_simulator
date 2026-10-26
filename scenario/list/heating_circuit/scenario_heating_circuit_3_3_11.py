from consoleLog import print_error, print_log
from scenario.base.filling_loop_alarm import FillingLoopAlarmScenario
import smartnet.constants as snc


class Scenario(FillingLoopAlarmScenario):
	PUMP_ALWAYS_ON = 2  # HeatingCircuitProgram::PUMP_MODE_ALWAYS_ON
	FLOW_TEMPERATURE = 30
	BOILER_TEMPERATURE = 60
	STATE_TIMEOUT = 120  # Includes the controller's 60 s pump off delay.
	HOLD_DURATION = 5

	def get_checklist_id(self):
		return '3.3.11'

	def get_default_preset(self):
		return 'heating_circuit_3_3_11'

	def get_scenario_title(self):
		return 'Heating circuit: circulation pump shutdown on alarm and recovery'

	def get_scenario_description(self):
		return (
			'Отопительный контур выключает насос циркуляции при аварии от программы '
			'подпитки и возобновляет работу после нормализации давления'
		)

	def get_required_programs(self):
		return {
			'heating_circuit': snc.ProgramType.HEATING_CIRCUIT,
			'boiler': snc.ProgramType.BOILER,
			'filling_loop': snc.ProgramType.FILLING_LOOP,
		}

	def _check_state(self, alarm, pump_on, description):
		print_log(description)
		expected = self.RELAY_ON if pump_on else self.RELAY_OFF
		if not self.wait_state_permanence(
			lambda: self._alarm_is(alarm) and self._pump.get_value() == expected,
			self.HOLD_DURATION, self.STATE_TIMEOUT,
		):
			print_error(f'Не подтверждено состояние: {description}')
			return False
		return True

	def _sequence(self):
		if not self._check_state(False, True, 'Нормальное давление: насос контура работает'):
			return False
		self._set_pressure(self.PRESSURE_LOW)
		if not self.wait_event(lambda: self._alarm_is(True), self.ALARM_TIMEOUT):
			print_error('Программа подпитки не сформировала аварию')
			return False
		if not self._check_state(True, False, 'Авария подпитки: насос контура выключен'):
			return False
		self._set_pressure(self.PRESSURE_NORMAL)
		return self._check_state(False, True, 'Давление восстановлено: насос контура снова работает')

	def run(self):
		circuit = self._programList['heating_circuit']
		boiler = self._programList['boiler']
		self._pump = circuit.get_output_channel('pump')
		settings = [
			(circuit, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.ALARM_PROGRAM_ID,
			 self._programList['filling_loop'].get_id()),
			(circuit, snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.PUMP_MODE,
			 self.PUMP_ALWAYS_ON),
		]
		sensors = [
			(circuit.get_input_channel('temperature'), self.FLOW_TEMPERATURE),
			(boiler.get_input_channel('temperature'), self.BOILER_TEMPERATURE),
		]
		self._run_alarm_test(settings, sensors, [self._pump], self._sequence)
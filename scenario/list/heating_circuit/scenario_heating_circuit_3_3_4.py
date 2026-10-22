import math

from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter
from smartnet.units import SENSOR_UNDEFINED


class Scenario(Parent):
	PUMP_MODE_STANDARD = 0  # HeatingCircuitProgram::PUMP_MODE_STANDARD
	PUMP_OFF_TEMPERATURE = 20
	OUTDOOR_MARGIN = 5  # Outside the controller's 1 C hysteresis band.
	FLOW_SETPOINT = 40
	TEMPERATURE_TOLERANCE = 1
	OUTDOOR_TIMEOUT = 6 * 60
	PUMP_OFF_DELAY = 60  # HeatingCircuitProgram::PUMP_OFF_DELAY
	STATE_TIMEOUT = 2 * 60
	STABLE_DURATION = 20

	def get_checklist_id(self):
		return '3.3.4'

	def get_default_preset(self):
		return 'heating_circuit_3_3_4'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'heating_circuit': snc.ProgramType.HEATING_CIRCUIT,
			'outdoor': snc.ProgramType.OUTDOOR_SENSOR,
			'boiler': snc.ProgramType.BOILER,
		}

	def get_scenario_title(self):
		return 'Heating circuit: summer mode switches pump by outdoor temperature'

	def get_scenario_description(self):
		return (
			'При +15 C насос и запрос тепла включены; при +25 C насос выключается '
			'с учётом штатной задержки и запрос тепла пропадает. '
			'При повторном похолодании до +15 C отопление возобновляется.'
		)

	def _read_parameter(self, program_type, parameter_id):
		parameter = RemoteControlParameter(
			programType=program_type, parameterId=parameter_id, programId=self._circuit.get_id(),
		)
		return parameter.get_value() if parameter.read() else None

	def _write_parameter(self, program_type, parameter_id, value):
		return RemoteControlParameter(
			programType=program_type, parameterId=parameter_id,
			programId=self._circuit.get_id(), parameterValue=value,
		).write()

	def _settings(self):
		return [
			(snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.PUMP_MODE, self.PUMP_MODE_STANDARD),
			(snc.ProgramType.HEATING_CIRCUIT, snc.HeatingCircuitParameterId.PUMP_OFF_OUTDOOR_TEMPERATURE, self.PUMP_OFF_TEMPERATURE),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.HEAT_CALCULATION_MODE, snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE),
			(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE, self.FLOW_SETPOINT),
		]

	def _outdoor_is_close(self, temperature):
		actual = self._read_parameter(snc.ProgramType.CIRCUIT, snc.CircuitParameterId.OUTDOOR_TEMPERATURE)
		return (
			isinstance(actual, (int, float)) and math.isfinite(actual)
			and abs(actual - temperature) <= self.TEMPERATURE_TOLERANCE
		)

	def _state_matches(self, temperature, heating):
		if not self._outdoor_is_close(temperature):
			return False
		request = self._read_parameter(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.REQUIRED_TEMPERATURE)
		if request is None:
			return False
		if heating:
			has_request = (
				isinstance(request, (int, float)) and math.isfinite(request)
				and 0 < request < 100 and request != SENSOR_UNDEFINED
			)
			return self._pump.get_value() == self.RELAY_ON and has_request
		return self._pump.get_value() == self.RELAY_OFF and request in (0, SENSOR_UNDEFINED, 'OPEN')

	def _check_phase(self, sensor, temperature, heating):
		print_log(f'Улица {temperature:+g} C: ожидаем отопление {"ВКЛ" if heating else "ВЫКЛ"}')
		sensor.set_value(temperature, True)
		if not self.wait_event(lambda: self._outdoor_is_close(temperature), self.OUTDOOR_TIMEOUT):
			print_error('Контур не принял заданную уличную температуру')
			return False
		timeout = self.STATE_TIMEOUT + (0 if heating else self.PUMP_OFF_DELAY)
		if not self.wait_state_permanence(
			lambda: self._state_matches(temperature, heating), self.STABLE_DURATION, timeout,
		):
			print_error('Насос и запрос тепла не перешли в ожидаемое устойчивое состояние')
			return False
		return True

	def run(self):
		self._status = 'FAIL'
		self._circuit = self._programList['heating_circuit']
		self._pump = self._circuit.get_output_channel('pump')
		sensor = self._programList['outdoor'].get_input_channel('outdoorTemperature')
		if not sensor.is_mapped() or not self._pump.is_mapped():
			print_error('Не найден уличный датчик или выход насоса контура')
			return
		initial_temperature = sensor.get_value()
		initial_manual = sensor.isManual()
		if (
			not isinstance(initial_temperature, (int, float)) or not math.isfinite(initial_temperature)
			or sensor.isShort() or sensor.isOpen()
		):
			print_error('Исходный уличный датчик должен иметь нормальную температуру')
			return
		settings = self._settings()
		saved = []
		for program_type, parameter_id, _ in settings:
			value = self._read_parameter(program_type, parameter_id)
			if value is None:
				print_error(f'Не прочитан исходный параметр {program_type}/{parameter_id}')
				return
			saved.append((program_type, parameter_id, value))
		try:
			for program_type, parameter_id, value in settings:
				if not self._write_parameter(program_type, parameter_id, value):
					print_error(f'Не записан параметр {program_type}/{parameter_id}')
					return
			# Do not register in _manualSensorsList: clear() must preserve restored manual mode.
			sensor.set_manual(True)
			cold = self.PUMP_OFF_TEMPERATURE - self.OUTDOOR_MARGIN
			hot = self.PUMP_OFF_TEMPERATURE + self.OUTDOOR_MARGIN
			for temperature, heating in ((cold, True), (hot, False), (cold, True)):
				if not self._check_phase(sensor, temperature, heating):
					return
			self._status = 'OK'
		finally:
			for program_type, parameter_id, value in reversed(saved):
				try:
					if not self._write_parameter(program_type, parameter_id, value):
						raise RuntimeError('нет подтверждения записи')
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен параметр {program_type}/{parameter_id}: {error}')
			try:
				sensor.set_value(initial_temperature, True)
			except Exception:
				self._status = 'FAIL'
				raise
			finally:
				sensor.set_manual(initial_manual)
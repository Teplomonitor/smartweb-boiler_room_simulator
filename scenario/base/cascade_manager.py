from contextlib import contextmanager
from math import isfinite

from consoleLog import print_error
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
import smartnet.remoteControl as sr


class CascadeManagerScenario(Parent):
	TEMPERATURE_TOLERANCE = 0.2
	RESPONSE_TIMEOUT = 90
	STABILITY_DURATION = 5

	def get_required_programs(self):
		return {
			'cascade': snc.ProgramType.CASCADE_MANAGER,
			'boiler_1': snc.ProgramType.BOILER,
			'boiler_2': snc.ProgramType.BOILER,
			'dhw': snc.ProgramType.DHW,
		}

	def get_default_preset(self):
		return 'cascade_manager_3_6_3'

	def force_preset_load(self):
		return True

	def read_parameter(self, program, program_type, parameter_id, index=None):
		parameter = sr.RemoteControlParameter(
			programType=program_type,
			parameterId=parameter_id,
			programId=program.get_id(),
			parameterIndex=index,
		)
		if not parameter.read():
			raise RuntimeError(f'Не удалось прочитать параметр {program_type}.{parameter_id}')
		value = parameter.get_value()
		if not isinstance(value, (int, float)) or not isfinite(value):
			raise RuntimeError(f'Некорректное значение параметра {program_type}.{parameter_id}: {value}')
		return value

	def write_parameter(self, program, program_type, parameter_id, value):
		parameter = sr.RemoteControlParameter(
			programType=program_type,
			parameterId=parameter_id,
			programId=program.get_id(),
			parameterValue=value,
		)
		if not parameter.write():
			raise RuntimeError(f'Не удалось записать параметр {program_type}.{parameter_id}')
		if self.read_parameter(program, program_type, parameter_id) != value:
			raise RuntimeError(f'Не подтверждено значение параметра {program_type}.{parameter_id}: {value}')

	def read_required_temperature(self):
		return self.read_parameter(
			self._programList['cascade'], snc.ProgramType.TEMPERATURE_SOURCE,
			snc.TemperatureSourceParameterId.REQUIRED_TEMPERATURE,
		)

	def read_required_power(self):
		power = self.read_parameter(
			self._programList['cascade'], snc.ProgramType.CASCADE_MANAGER,
			snc.CascadeManagerParameterId.REQUIRED_POWER,
		)
		if not 0 <= power <= 100:
			raise RuntimeError(f'Требуемая мощность вне диапазона 0–100%: {power}')
		return power

	def required_temperature_is(self, expected):
		return abs(self.read_required_temperature() - expected) <= self.TEMPERATURE_TOLERANCE

	def require_stable(self, condition, description):
		if not self.wait_state_permanence(condition, self.STABILITY_DURATION, self.RESPONSE_TIMEOUT):
			raise RuntimeError(description)

	@contextmanager
	def test_configuration(self, settings, sensors):
		# Read everything before modifying anything; a failed write may still have
		# reached the controller, so include it in the restoration list as well.
		original_settings = [
			(program, program_type, parameter_id, self.read_parameter(program, program_type, parameter_id))
			for program, program_type, parameter_id, value in settings
		]
		original_sensors = []
		for sensor in sensors:
			value = sensor.get_value()
			if (
				not sensor.is_mapped() or sensor.isShort() or sensor.isOpen()
				or not isinstance(value, (int, float)) or not isfinite(value)
			):
				raise RuntimeError('Не найден исправный датчик с числовой температурой')
			original_sensors.append((sensor, value, sensor.isManual()))
		attempted_settings = []
		try:
			for setting, original in zip(settings, original_settings):
				attempted_settings.append(original)
				self.write_parameter(*setting)
			yield
		finally:
			for original in reversed(attempted_settings):
				try:
					self.write_parameter(*original)
				except Exception as exc:
					print_error(f'Не удалось восстановить настройку каскадного теста: {exc}')
					self._status = 'FAIL'
			for sensor, value, manual in original_sensors:
				try:
					try:
						sensor.set_manual(True)
						sensor.set_value(value, True)
					finally:
						sensor.set_manual(manual)
				except Exception as exc:
					print_error(f'Не удалось восстановить датчик каскадного теста: {exc}')
					self._status = 'FAIL'
				finally:
					if sensor in self._manualSensorsList:
						self._manualSensorsList.remove(sensor)
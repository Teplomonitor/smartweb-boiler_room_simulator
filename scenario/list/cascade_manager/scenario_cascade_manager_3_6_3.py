from consoleLog import print_error, print_log
from scenario.base.cascade_manager import CascadeManagerScenario
import smartnet.constants as snc


class Scenario(CascadeManagerScenario):
	PROPORTIONAL_BAND = 20
	INTEGRAL_FACTOR = 100
	DHW_TEMPERATURE = 20
	DHW_SETPOINT = 50
	HIGH_DHW_SETPOINT = 54
	MAXIMUM_REQUIRED_TEMPERATURE = 90
	POWER_TOLERANCE = 2
	INTEGRAL_POWER_INCREASE = 3
	INTEGRAL_TIMEOUT = 60
	INTEGRAL_POWER_LIMIT = 40
	# Expected percentages for a 20 °C proportional band, below the 50%
	# capacity of one of two equal boilers. No second-source delay is involved.
	PROPORTIONAL_CASES = ((48, 10), (44, 30), (48, 10), (50, 0), (55, 0), (48, 10))

	def get_scenario_title(self):
		return 'Cascade manager: required power follows current and required temperatures'

	def get_scenario_description(self):
		return (
			'Рассчитывает требуемую мощность в зависимости от текущей и требуемой '
			'температур: проверка P-регулирования и накопления I-составляющей; D выключено'
		)

	def get_checklist_id(self):
		return '3.6.3'

	def sources_are_ready(self):
		cascade = self._programList['cascade']
		powers = []
		for index, name in enumerate(('boiler_1', 'boiler_2')):
			source_id = self.read_parameter(
				cascade, snc.ProgramType.CASCADE_MANAGER,
				snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID, index,
			)
			if source_id != self._programList[name].get_id():
				return False
			powers.append(self.read_parameter(
				cascade, snc.ProgramType.CASCADE_MANAGER,
				snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_POWER, index,
			))
		return powers[0] > 0 and powers[0] == powers[1]

	def check_power(self, expected_temperature, expected_power):
		print_log(f'Ожидаем запрос {expected_temperature} °C и мощность {expected_power}%')
		self.require_stable(
			lambda: (
				self.required_temperature_is(expected_temperature)
				and abs(self.read_required_power() - expected_power) <= self.POWER_TOLERANCE
			),
			f'Неверный расчёт мощности: ожидалось {expected_power}% при запросе {expected_temperature} °C',
		)
		print_log(f'Требуемая мощность: {self.read_required_power()}%')

	def run(self):
		self._status = 'FAIL'
		cascade = self._programList['cascade']
		dhw = self._programList['dhw']
		collector = cascade.get_input_channel('temperature')
		dhw_sensor = dhw.get_temperature()
		parameter_type = snc.ProgramType.CASCADE_MANAGER
		parameter_id = snc.CascadeManagerParameterId
		settings = [
			(cascade, parameter_type, parameter_id.PARAM_I_FACTOR, 0),
			(cascade, parameter_type, parameter_id.PARAM_D_FACTOR, 0),
			(cascade, parameter_type, parameter_id.PARAM_P_FACTOR, self.PROPORTIONAL_BAND),
			(cascade, parameter_type, parameter_id.WORK_FUNCTION, 0),  # STANDARD
			(cascade, parameter_type, parameter_id.ROTATION_TYPE, 0),  # OFF
			(cascade, parameter_type, parameter_id.TEMPERATURE_OFFSET, 0),
			(cascade, parameter_type, parameter_id.MINIMUM_REQUIRED_TEMPERATURE, 0),
			(cascade, parameter_type, parameter_id.MAXIMUM_REQUIRED_TEMPERATURE, self.MAXIMUM_REQUIRED_TEMPERATURE),
			(dhw, snc.ProgramType.CONSUMER, snc.ConsumerParameterId.TEMPERATURE_COMPENSATION, 0),
			(dhw, snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT, self.DHW_SETPOINT),
			(dhw, snc.ProgramType.DHW, snc.DhwParameterId.WORK_MODE, 0),  # COMFORT
		]
		try:
			for name in ('boiler_1', 'boiler_2'):
				boiler = self._programList[name]
				if any(boiler.get_input_channel(channel).is_mapped() for channel in ('temperature', 'backwardTemperature')):
					raise RuntimeError('Котлы каскада должны быть без собственных датчиков температуры')
			with self.test_configuration(settings, (collector, dhw_sensor)):
				self.set_sensor_value(dhw_sensor, self.DHW_TEMPERATURE)
				self.set_sensor_value(collector, self.PROPORTIONAL_CASES[0][0])
				self.require_stable(self.sources_are_ready, 'Менеджер не обнаружил два котла одинаковой мощности')

				for temperature, power in self.PROPORTIONAL_CASES:
					print_log(f'P-регулирование: температура коллектора {temperature} °C')
					self.set_sensor_value(collector, temperature)
					self.check_power(self.DHW_SETPOINT, power)

				print_log('Меняем запрос ГВС при неизменной температуре коллектора')
				self.write_parameter(dhw, snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT, self.HIGH_DHW_SETPOINT)
				self.check_power(self.HIGH_DHW_SETPOINT, 30)
				self.write_parameter(dhw, snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT, self.DHW_SETPOINT)
				self.check_power(self.DHW_SETPOINT, 10)

				# I=0 has cleared the integrator. Keep both temperatures fixed;
				# a rise now must come from integration, not a changing heat demand.
				baseline = self.read_required_power()
				self.write_parameter(cascade, parameter_type, parameter_id.PARAM_I_FACTOR, self.INTEGRAL_FACTOR)
				print_log(f'PI-регулирование: ждём роста мощности минимум на {self.INTEGRAL_POWER_INCREASE} п.п.')
				def integral_power_has_grown():
					power = self.read_required_power()
					return (
						self.required_temperature_is(self.DHW_SETPOINT)
						and baseline + self.INTEGRAL_POWER_INCREASE <= power < self.INTEGRAL_POWER_LIMIT
					)
				if not self.wait_event(integral_power_has_grown, self.INTEGRAL_TIMEOUT):
					raise RuntimeError(f'I-составляющая не увеличила мощность: исходная {baseline}%, текущая {self.read_required_power()}%')
				print_log(f'I-составляющая увеличила мощность до {self.read_required_power()}%')
				self._status = 'OK'
		except RuntimeError as exc:
			print_error(str(exc))
			self._status = 'FAIL'
		if self._status == 'OK':
			print_log('Расчёт требуемой мощности каскада по температурам проверен (P и PI)')
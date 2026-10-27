from consoleLog import print_log, print_error
from scenario.base.swimming_pool import PoolScenario


class Scenario(PoolScenario):
	MODE_COMFORT = 0
	CIRCULATION_ON = 0
	TEST_TEMPERATURE = 28
	# Гистерезис контроллера — 1 °C; проверяем вне его границ.
	TEMPERATURE_OFFSET = 2
	TEMPERATURE_TOLERANCE = 0.1
	PARAMETER_TIMEOUT = 30
	PUMP_SWITCH_TIMEOUT = 60
	PUMP_STABLE_DURATION = 5

	def get_scenario_title(self):
		return 'pool test 3 - loading pump temperature control'

	def get_scenario_description(self):
		return 'Включает/выключает насос загрузки в зависимости от текущей и требуемой температуры'

	def get_checklist_id(self):
		return '3.11.3'

	def set_parameter(self, name, value):
		if self._pool.write_parameter_value(name, value) is None:
			print_error(f'Не удалось записать параметр бассейна {name}: {value}')
			return False
		return True

	def set_required_temperature(self, value):
		if not self.set_parameter('requiredPoolTemperatureComfort', value):
			return False

		def temperature_matches():
			actual = self.read_required_pool_temperature()
			return actual is not None and abs(actual - value) <= self.TEMPERATURE_TOLERANCE

		if not self.wait_event(temperature_matches, self.PARAMETER_TIMEOUT):
			print_error(f'Требуемая температура бассейна не стала равна {value} °C')
			return False
		return True

	def check_loading_pump(self, expected_on):
		state_title = 'включён' if expected_on else 'выключен'
		print_log(f'Ждём, что насос загрузки будет {state_title}')

		def state_matches():
			state = self.get_loading_pump_state()
			return state is not None and (state != self.RELAY_OFF) == expected_on

		if not self.wait_state_permanence(
			state_matches, self.PUMP_STABLE_DURATION, self.PUMP_SWITCH_TIMEOUT
		):
			print_error(f'Насос загрузки не перешёл в устойчивое состояние: {state_title}')
			return False
		print_log(f'Хорошо, насос загрузки {state_title}')
		return True

	def run(self):
		self._status = 'FAIL'
		sensor = self._pool.get_temperature()
		if not sensor.is_mapped() or not self._pool.getLoadingPumpState().is_mapped():
			print_error('Для проверки нужны датчик температуры и выход насоса загрузки')
			return

		original_parameters = {}
		for name in ('workMode', 'circulationPumpWorkMode', 'requiredPoolTemperatureComfort'):
			value = self._pool.read_parameter_value(name)
			if value is None:
				print_error(f'Не удалось прочитать исходный параметр бассейна {name}')
				return
			original_parameters[name] = value
		original_temperature = sensor.get_value()

		try:
			if not self.set_parameter('workMode', self.MODE_COMFORT):
				return
			if not self.set_parameter('circulationPumpWorkMode', self.CIRCULATION_ON):
				return
			if not self.set_required_temperature(self.TEST_TEMPERATURE):
				return

			print_log('Блок 1: меняем температуру воды при неизменной уставке 28 °C')
			for offset, expected_on in (
				(self.TEMPERATURE_OFFSET, False),
				(-self.TEMPERATURE_OFFSET, True),
				(self.TEMPERATURE_OFFSET, False),
			):
				temperature = self.TEST_TEMPERATURE + offset
				print_log(f'Задаём температуру воды {temperature} °C')
				self.set_pool_temperature(temperature)
				if not self.check_loading_pump(expected_on):
					return

			print_log('Блок 2: меняем уставку при неизменной температуре воды 28 °C')
			self.set_pool_temperature(self.TEST_TEMPERATURE)
			for offset, expected_on in (
				(-self.TEMPERATURE_OFFSET, False),
				(self.TEMPERATURE_OFFSET, True),
				(-self.TEMPERATURE_OFFSET, False),
			):
				required_temperature = self.TEST_TEMPERATURE + offset
				print_log(f'Задаём требуемую температуру {required_temperature} °C')
				if not self.set_required_temperature(required_temperature):
					return
				if not self.check_loading_pump(expected_on):
					return

			self._status = 'OK'
			print_log('Хорошо! Насос загрузки реагирует отдельно на температуру воды и уставку')
		finally:
			print_log('Восстанавливаем исходные настройки бассейна')
			try:
				# Режим восстанавливаем последним, после уставки и циркуляции.
				for name in ('requiredPoolTemperatureComfort', 'circulationPumpWorkMode', 'workMode'):
					if not self.set_parameter(name, original_parameters[name]):
						self._status = 'FAIL'
			finally:
				try:
					if original_temperature is not None:
						sensor.set_value(original_temperature, True)
				finally:
					sensor.set_manual(False)
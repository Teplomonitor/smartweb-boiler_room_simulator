from scenario.base.heating_circuit_demand import HeatingCircuitDemandScenario


class Scenario(HeatingCircuitDemandScenario):
	def get_checklist_id(self):
		return '3.3.5.2'

	def get_scenario_title(self):
		return 'Heating circuit: room correction at fixed outdoor temperature'

	def get_scenario_description(self):
		return (
			'При постоянной улице 0 C и погодном режиме недогрев помещения повышает '
			'запрос, перегрев снижает. Проверяются изменение комнатной уставки '
			'и дальнейшее накопление коррекции при постоянной ошибке обоих знаков.'
		)

	def _sequence(self):
		# Weather demand=36 C; proportional room gain=1+0.8=1.8.
		for room, setpoint, expected in (
			(20, 20, 36), (18, 20, 39.6), (22, 20, 32.4),
			(20, 20, 36), (20, 22, 39.6), (20, 18, 32.4), (20, 20, 36),
		):
			self._check_point(0, room, setpoint, expected)
		self._check_integral(0, 18, 39.6)
		self._check_integral(0, 22, 32.4)

	def run(self):
		self._run_test(self._sequence)
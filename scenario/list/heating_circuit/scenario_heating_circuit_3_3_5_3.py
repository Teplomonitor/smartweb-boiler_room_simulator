from scenario.base.heating_circuit_demand import HeatingCircuitDemandScenario
import smartnet.constants as snc


class Scenario(HeatingCircuitDemandScenario):
	LIMITED_ROOM_SHIFT = 2
	LIMITED_MINIMUM_FLOW = 35
	LIMITED_MAXIMUM_FLOW = 40

	def get_checklist_id(self):
		return '3.3.5.3'

	def get_scenario_title(self):
		return 'Heating circuit: combined weather and room demand'

	def get_scenario_description(self):
		return (
			'Погодный график задаёт основу запроса, комнатное отклонение корректирует её '
			'при потеплении и похолодании. Проверяются границы коррекции и подачи, '
			'сохранение накопленной поправки при достижении уставки и смене улицы.'
		)

	def _sequence(self):
		for outdoor, room, expected in (
			(10, 20, 28.6), (10, 18, 32.2), (-10, 18, 45.9),
			(-10, 22, 38.7), (10, 22, 25), (0, 20, 36),
		):
			self._check_point(outdoor, room, self.ROOM_SETPOINT, expected)

		parameter = snc.CircuitParameterId
		self._set_circuit(parameter.ROOM_SENSOR_INFLUENCE_MIN, -self.LIMITED_ROOM_SHIFT)
		self._set_circuit(parameter.ROOM_SENSOR_INFLUENCE_MAX, self.LIMITED_ROOM_SHIFT)
		self._check_point(0, 16, self.ROOM_SETPOINT, 38)
		self._check_point(0, 24, self.ROOM_SETPOINT, 34)
		self._set_circuit(parameter.ROOM_SENSOR_INFLUENCE_MIN, -self.ROOM_SHIFT_LIMIT)
		self._set_circuit(parameter.ROOM_SENSOR_INFLUENCE_MAX, self.ROOM_SHIFT_LIMIT)

		self._set_circuit(parameter.MINIMUM_FLOW_TEMPERATURE, self.LIMITED_MINIMUM_FLOW)
		self._set_circuit(parameter.MAXIMUM_FLOW_TEMPERATURE, self.LIMITED_MAXIMUM_FLOW)
		self._check_point(10, 20, self.ROOM_SETPOINT, self.LIMITED_MINIMUM_FLOW)
		self._check_point(-10, 20, self.ROOM_SETPOINT, self.LIMITED_MAXIMUM_FLOW)
		self._set_circuit(parameter.MINIMUM_FLOW_TEMPERATURE, self.MINIMUM_FLOW)
		self._set_circuit(parameter.MAXIMUM_FLOW_TEMPERATURE, self.MAXIMUM_FLOW)

		request = self._check_integral(0, 18, 39.6)
		# At the room setpoint P disappears, but I must remain; do not reset it.
		integral_shift = request - 39.6
		self._check_point(0, 20, self.ROOM_SETPOINT, 36 + integral_shift, reset_integral=False)
		self._check_point(10, 20, self.ROOM_SETPOINT, 28.6 + integral_shift, reset_integral=False)

	def run(self):
		self._run_test(self._sequence)
from scenario.base.heat_dump import HeatDumpScenario


class Scenario(HeatDumpScenario):
	def get_scenario_title(self):
		return '6.5.2 Комната: температурное управление при запрете сброса'

	def get_scenario_description(self):
		return 'При запрете сброса для клапана он закрыт в жаре и открывается при холоде'

	def get_checklist_id(self):
		return '6.5.2'

	def run(self):
		circuit = self._programList['circuit']
		room = self._programList['room_1']
		valve = room.get_output_channel('valve1')
		sensor = room.get_temperature()
		# The circuit still forwards cooling; only this room valve forbids heat extrication.
		settings = self.circuit_settings() + self.room_settings('room_1', 0, False)
		sensors = [(circuit.get_input_channel('temperature'), 30),
			(sensor, self.ROOM_TEMPERATURE)]
		def baseline():
			self.expect(valve, self.RELAY_OFF, 'Клапан горячей комнаты до сброса', self.ROOM_TIMEOUT)
		def active():
			self.expect(valve, self.RELAY_OFF, 'Клапан горячей комнаты при запрете', self.ROOM_TIMEOUT)
			sensor.set_value(self.ROOM_SETPOINT - 5, True)
			self.expect(valve, lambda value: value != self.RELAY_OFF,
				'Клапан остывшей комнаты', self.ROOM_TIMEOUT)
			sensor.set_value(self.ROOM_TEMPERATURE, True)
			self.expect(valve, self.RELAY_OFF, 'Клапан снова горячей комнаты', self.ROOM_TIMEOUT)
		self.run_heat_dump(settings, sensors, baseline, active)
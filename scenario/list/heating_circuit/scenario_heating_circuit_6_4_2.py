from scenario.base.heat_dump import HeatDumpScenario


class Scenario(HeatDumpScenario):
	def get_scenario_title(self):
		return '6.4.2 Отопительный контур: запрос охлаждения всем комнатам'

	def get_scenario_description(self):
		return 'При сбросе тепла обе привязанные комнаты открывают свои клапаны'

	def get_checklist_id(self):
		return '6.4.2'

	def run(self):
		circuit = self._programList['circuit']
		room_1 = self._programList['room_1']
		room_2 = self._programList['room_2']
		valves = (room_1.get_output_channel('valve1'), room_2.get_output_channel('valve2'))
		settings = (self.circuit_settings() + self.room_settings('room_1', 0, True)
			+ self.room_settings('room_2', 1, True))
		sensors = [(circuit.get_input_channel('temperature'), 30),
			(room_1.get_temperature(), self.ROOM_TEMPERATURE),
			(room_2.get_temperature(), self.ROOM_TEMPERATURE)]
		def baseline():
			for index, valve in enumerate(valves, 1):
				self.expect(valve, self.RELAY_OFF, f'Клапан комнаты {index} до сброса', self.ROOM_TIMEOUT)
		def active():
			for index, valve in enumerate(valves, 1):
				self.expect(valve, lambda value: value != self.RELAY_OFF,
					f'Клапан комнаты {index} после запроса', self.ROOM_TIMEOUT)
		self.run_heat_dump(settings, sensors, baseline, active, observe_rooms=True)
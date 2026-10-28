from scenario.base.heat_dump import HeatDumpScenario


class Scenario(HeatDumpScenario):
	def get_scenario_title(self):
		return '6.5.1 Комната: открытие клапана при разрешённом сбросе'

	def get_scenario_description(self):
		return 'Горячая комната открывает клапан по запросу разрешённого сброса тепла'

	def get_checklist_id(self):
		return '6.5.1'

	def run(self):
		circuit = self._programList['circuit']
		room = self._programList['room_1']
		valve = room.get_output_channel('valve1')
		settings = self.circuit_settings() + self.room_settings('room_1', 0, True)
		sensors = [(circuit.get_input_channel('temperature'), 30),
			(room.get_temperature(), self.ROOM_TEMPERATURE)]
		def baseline():
			self.expect(valve, self.RELAY_OFF, 'Клапан горячей комнаты до сброса', self.ROOM_TIMEOUT)
		def active():
			self.expect(valve, lambda value: value != self.RELAY_OFF,
				'Клапан горячей комнаты после сброса', self.ROOM_TIMEOUT)
		self.run_heat_dump(settings, sensors, baseline, active)
from scenario.base.heat_dump import HeatDumpFailed, HeatDumpScenario
import smartnet.constants as snc


class Scenario(HeatDumpScenario):
	ESTIMATED_RUN_SECONDS = 120
	NORMALLY_CLOSED_VALVE_STATE = 1

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
		valve_settings = []
		def expect_valves(opened, label):
			for index, (valve, setting) in enumerate(zip(valves, valve_settings), 1):
				normally_open = setting == self.NORMALLY_OPEN_VALVE_STATE
				energized = normally_open != opened
				expected = (lambda value: value in (self.RELAY_MAX, self.RELAY_ON)) if energized else self.RELAY_OFF
				self.expect(valve, expected, f'Клапан комнаты {index} {label}', self.ROOM_TIMEOUT)
		def baseline():
			for index, room in enumerate((room_1, room_2), 1):
				setting = self._read(room, snc.ProgramType.ROOM_DEVICE,
					snc.RoomDeviceParameterId.ROOM_DEVICE_VALVE_STATE)
				if setting not in (self.NORMALLY_OPEN_VALVE_STATE, self.NORMALLY_CLOSED_VALVE_STATE):
					raise HeatDumpFailed(f'Неизвестная настройка клапана комнаты {index}: {setting}')
				valve_settings.append(setting)
			expect_valves(False, 'до сброса')
		def active():
			expect_valves(True, 'после запроса')
		self.run_heat_dump(settings, sensors, baseline, active, observe_rooms=True)
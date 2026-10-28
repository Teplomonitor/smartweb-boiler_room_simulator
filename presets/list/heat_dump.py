"""Consumers of a simulator-injected cooling request (no real boiler program)."""

import smartnet.constants as snc
from smartnet.channelMapping import ChannelMapping
from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import DhwSettings, HeatingCircuitSettings, RoomSettings, SnowMelterSettings, SwimmingPoolSettings


SOURCE_ID = 200
CIRCUIT_ID = 104


def get_presets_list():
	def sensor(index):
		return ChannelMapping(index, 'CHANNEL_SENSOR', 123)

	def output(index, host):
		return ChannelMapping(index, 'CHANNEL_RELAY', host)

	programs = [
		ProgramPreset(snc.ProgramType.DHW, 'DEFAULT', 101, 'Heat dump DHW',
			DhwSettings(SOURCE_ID), [sensor(0)],
			[output(0, 123), output(1, 123), output(2, 123)]),
		ProgramPreset(snc.ProgramType.SNOWMELT, 'DEFAULT', 102, 'Heat dump snow',
			SnowMelterSettings(SOURCE_ID), [sensor(1), sensor(2), sensor(3)],
			[output(0, 124), output(1, 124), output(2, 124)]),
		ProgramPreset(snc.ProgramType.POOL, 'DEFAULT', 103, 'Heat dump pool',
			SwimmingPoolSettings(SOURCE_ID), [sensor(4)],
			[output(3, 123), output(4, 123)]),
		ProgramPreset(snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_DIRECT', CIRCUIT_ID,
			'Heat dump circuit', HeatingCircuitSettings(source=SOURCE_ID),
			[sensor(5)], [None, None, None, output(3, 124)]),
		ProgramPreset(snc.ProgramType.ROOM_DEVICE, 'DEFAULT', 105, 'Heat dump room 1',
			RoomSettings(source_1=CIRCUIT_ID, source_2=0, source_3=0),
			[sensor(6)], [output(0, 125)]),
		ProgramPreset(snc.ProgramType.ROOM_DEVICE, 'DEFAULT', 106, 'Heat dump room 2',
			RoomSettings(source_1=0, source_2=CIRCUIT_ID, source_3=0),
			[sensor(7)], [None, output(1, 125)]),
	]
	controllers = [ControllerPreset('SWK_1', host, f'SWK_{host}') for host in (123, 124, 125)]
	return programs, controllers
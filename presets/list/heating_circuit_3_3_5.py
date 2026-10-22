from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc
from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import HeatingCircuitSettings, RoomSettings


HOST_ID = 123
CIRCUIT_ID = 101
BOILER_ID = 102
OUTDOOR_ID = 103
ROOM_ID = 104


def get_presets_list():
	def sensor(channel_id):
		return ChannelMapping(channel_id, 'CHANNEL_SENSOR', HOST_ID)

	def relay(channel_id):
		return ChannelMapping(channel_id, 'CHANNEL_RELAY', HOST_ID)

	programs = [
		ProgramPreset(
			snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_MIXED', CIRCUIT_ID,
			'Circuit 3.3.5', HeatingCircuitSettings(
				source=BOILER_ID, heatingSlope=0.8, temperatureCompensation=0,
				heatCalculationMode=snc.ConsumerHeatCalculationMode.WEATHER_HEATING_SLOPE,
			),
			[sensor(0)], [relay(0), None, None, relay(1)],
		),
		ProgramPreset(
			snc.ProgramType.BOILER, 'DEFAULT', BOILER_ID, 'Source 3.3.5',
			None, [sensor(1)], [None, relay(2)],
		),
		ProgramPreset(
			snc.ProgramType.OUTDOOR_SENSOR, 'DEFAULT', OUTDOOR_ID, 'Outdoor 3.3.5',
			None, [sensor(2)], [],
		),
		ProgramPreset(
			snc.ProgramType.ROOM_DEVICE, 'DEFAULT', ROOM_ID, 'Room 3.3.5',
			RoomSettings(source_1=CIRCUIT_ID, source_2=0, source_3=0), [sensor(3)], [],
		),
	]
	return programs, [ControllerPreset('SWK_1', HOST_ID, f'SWK_{HOST_ID}')]
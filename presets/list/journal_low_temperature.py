from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import CascadeSettings, HeatingCircuitSettings, RoomSettings
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


HOST_ID = 123
CIRCUIT_ID = 101
CASCADE_ID = 102
BOILER_ID = 103
ROOM_ID = 104


def get_presets_list():
	def sensor(index):
		return ChannelMapping(index, 'CHANNEL_SENSOR', HOST_ID)

	def relay(index):
		return ChannelMapping(index, 'CHANNEL_RELAY', HOST_ID)

	def unmapped():
		return ChannelMapping(0, 'CHANNEL_UNDEFINED', 0)

	programs = [
		ProgramPreset(
			snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_DIRECT', CIRCUIT_ID, 'Journal cold circuit',
			HeatingCircuitSettings(source=CASCADE_ID,
				heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
				requiredConstantFlowTemperature=60, temperatureCompensation=0),
			[sensor(0)], [unmapped(), unmapped(), unmapped(), relay(0)],
		),
		ProgramPreset(snc.ProgramType.CASCADE_MANAGER, 'DEFAULT', CASCADE_ID, 'Journal cascade',
			CascadeSettings(BOILER_ID), [sensor(1)], []),
		# A low return temperature excludes MLC_BOILER_POWER_IS_LOW at 50 minutes.
		ProgramPreset(snc.ProgramType.BOILER, 'DEFAULT', BOILER_ID, 'Journal cold boiler',
			None, [sensor(2), sensor(3)], [relay(1), relay(2)]),
		ProgramPreset(snc.ProgramType.ROOM_DEVICE, 'DEFAULT', ROOM_ID, 'Journal cold room',
			RoomSettings(source_1=0, source_2=0, source_3=0), [sensor(4)], []),
	]
	return programs, [ControllerPreset('SWK_1', HOST_ID, 'SWK_123')]
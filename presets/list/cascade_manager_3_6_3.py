from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import CascadeSettings, DhwSettings
from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc


HOST_ID = 123
DHW_ID = 101
CASCADE_ID = 102
BOILER_IDS = (103, 104)


def sensor_mapping(channel_id):
	return Mapping(channel_id, 'CHANNEL_SENSOR', HOST_ID)


def relay_mapping(channel_id):
	return Mapping(channel_id, 'CHANNEL_RELAY', HOST_ID)


def unmapped_channel():
	return Mapping(0, 'CHANNEL_UNDEFINED', 0)


def get_presets_list():
	programs = [
		ProgramPreset(
			snc.ProgramType.DHW, 'DEFAULT', DHW_ID, 'Cascade test consumer',
			DhwSettings(CASCADE_ID),
			[sensor_mapping(0)], [relay_mapping(0)],
		),
		ProgramPreset(
			snc.ProgramType.CASCADE_MANAGER, 'DEFAULT', CASCADE_ID, 'Cascade test',
			CascadeSettings(*BOILER_IDS),
			[sensor_mapping(1), unmapped_channel()], [],
		),
	]
	for index, boiler_id in enumerate(BOILER_IDS):
		programs.append(ProgramPreset(
			snc.ProgramType.BOILER, 'DEFAULT', boiler_id, f'Cascade boiler {index + 1}',
			None,
			# No local temperature control, external demand or alarm input.
			[unmapped_channel() for _ in range(4)],
			# Pump, unused discrete stages, modulating power output.
			[relay_mapping(1 + index * 2), unmapped_channel(), unmapped_channel(),
			 relay_mapping(2 + index * 2)],
		))
	return programs, [ControllerPreset('SWK_1', HOST_ID, 'SWK_123')]
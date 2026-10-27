"""Flow-through DHW priority test with a mapped boiler temperature source."""

import smartnet.constants as snc
from smartnet.channelMapping import ChannelMapping as Mapping
import presets.preset
from presets.settings import DhwSettings


HOST_DHW = 123
HOST_BOILER = 124
DHW_ID = 101
BOILER_ID = 102


def sensor(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)


def relay(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_RELAY', host_id)


def get_presets_list():
	programs = [
		presets.preset.ProgramPreset(
			snc.ProgramType.DHW, 'PROGRAM_SCHEME_1', DHW_ID, 'DHW priority flow-through',
			DhwSettings(BOILER_ID),
			[sensor(0, HOST_DHW), sensor(1, HOST_DHW), sensor(2, HOST_DHW)],
			[None, relay(3, HOST_DHW), relay(2, HOST_DHW), None, None],
		),
		presets.preset.ProgramPreset(
			snc.ProgramType.BOILER, 'DEFAULT', BOILER_ID, 'Priority test boiler', None,
			[sensor(0, HOST_BOILER)],
			[relay(0, HOST_BOILER), relay(1, HOST_BOILER), relay(2, HOST_BOILER)],
		),
	]
	controllers = [
		presets.preset.ControllerPreset('SWK_1', HOST_DHW, f'SWK_{HOST_DHW}'),
		presets.preset.ControllerPreset('SWK_1', HOST_BOILER, f'SWK_{HOST_BOILER}'),
	]
	return programs, controllers

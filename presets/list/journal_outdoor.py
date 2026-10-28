from presets.preset import ControllerPreset, ProgramPreset
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


CONTROLLER_ID = 123
OUTDOOR_ID = 101


def get_presets_list():
	return [
		ProgramPreset(
			snc.ProgramType.OUTDOOR_SENSOR, 'DEFAULT', OUTDOOR_ID,
			'Outdoor sensor', None,
			[ChannelMapping(0, 'CHANNEL_SENSOR', CONTROLLER_ID)], [],
		),
	], [ControllerPreset('SWK_1', CONTROLLER_ID, 'SWK_123')]
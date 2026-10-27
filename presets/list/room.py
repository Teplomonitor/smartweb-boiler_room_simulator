from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc
from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import RoomSettings


HOST_ID = 123
ROOM_IDS = (101, 102, 103, 104)


def get_presets_list():
	programs = [
		ProgramPreset(
			snc.ProgramType.ROOM_DEVICE, 'DEFAULT', room_id, f'Room {index + 1}',
			RoomSettings(source_1=0, source_2=0, source_3=0),
			[ChannelMapping(index, 'CHANNEL_SENSOR', HOST_ID)], [],
		)
		for index, room_id in enumerate(ROOM_IDS)
	]
	return programs, [ControllerPreset('SWK_1', HOST_ID, f'SWK_{HOST_ID}')]

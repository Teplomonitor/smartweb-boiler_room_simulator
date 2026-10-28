from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc

from presets.preset import ControllerPreset, ProgramPreset


def get_presets_list():
	controllers = [
		ControllerPreset('SWK_1', 123, 'SWK_123'),
		ControllerPreset('SWK_1', 124, 'SWK_124'),
	]
	inputs = [
		ChannelMapping(index, 'CHANNEL_SENSOR', 123)
		for index in range(6)
	] + [
		ChannelMapping(index, 'CHANNEL_SENSOR', 124)
		for index in range(3)
	]
	programs = [ProgramPreset(
		snc.ProgramType.ALARM, 'DEFAULT', 101, 'Сигнализация',
		None, inputs, [],
	)]
	return programs, controllers
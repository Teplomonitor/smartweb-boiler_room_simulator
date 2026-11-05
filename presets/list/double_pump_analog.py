from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc

from presets.preset import ControllerPreset, ProgramPreset


def get_presets_list():
	controller_id = 123
	inputs = [ChannelMapping(index, 'CHANNEL_SENSOR', controller_id) for index in range(4)]
	outputs = [
		None,
		None,
		ChannelMapping(0, 'CHANNEL_RELAY', controller_id),
		ChannelMapping(1, 'CHANNEL_RELAY', controller_id),
		ChannelMapping(2, 'CHANNEL_RELAY', controller_id),
	]
	programs = [ProgramPreset(
		snc.ProgramType.DOUBLE_PUMP, 'DEFAULT', 101, 'Сдвоенный насос (аналоговый)',
		None, inputs, outputs,
	)]
	controllers = [ControllerPreset('SWK_1', controller_id, 'SWK_123')]
	return programs, controllers
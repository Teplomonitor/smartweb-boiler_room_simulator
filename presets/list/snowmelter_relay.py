"""Snowmelt priority tests with a relay-driven loading pump."""

from presets.list import snowmelter
from presets.preset import ProgramPreset
from smartnet.channelMapping import ChannelMapping


def get_presets_list():
	programs, controllers = snowmelter.get_presets_list()
	analog = programs[0]
	programs[0] = ProgramPreset(
		analog.get_type(), analog.get_scheme(), analog.get_id(),
		analog.get_title(), analog.getSettings(), analog.get_inputs(),
		[ChannelMapping(0, 'CHANNEL_RELAY', snowmelter.hostId['HOST_1']),
			analog.getOutput(1), None],
	)
	return programs, controllers
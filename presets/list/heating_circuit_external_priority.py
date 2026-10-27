"""Priority circuits with an outdoor sensor for frost-protection checks."""

from presets.list.heating_circuit_priority import HOST_ID, get_presets_list as get_circuits
from presets.preset import ProgramPreset
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


def get_presets_list():
	programs, controllers = get_circuits()
	programs.append(ProgramPreset(
		snc.ProgramType.OUTDOOR_SENSOR, 'DEFAULT', 105, 'Priority outdoor sensor',
		None, [ChannelMapping(2, 'CHANNEL_SENSOR', HOST_ID)], [],
	))
	return programs, controllers
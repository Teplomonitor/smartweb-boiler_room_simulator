"""Standard DHW and its generator, without unrelated pressure alarms."""

from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import DhwSettings
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


HOST_ID = 123
BOILER_ID = 102


def get_presets_list():
	def sensor(channel):
		return ChannelMapping(channel, 'CHANNEL_SENSOR', HOST_ID)

	def relay(channel):
		return ChannelMapping(channel, 'CHANNEL_RELAY', HOST_ID)

	return [
		ProgramPreset(snc.ProgramType.DHW, 'DEFAULT', 101, 'DHW external priority',
			DhwSettings(BOILER_ID), [sensor(0)], [relay(0), relay(1)]),
		ProgramPreset(snc.ProgramType.BOILER, 'DEFAULT', BOILER_ID, 'DHW heat source',
			None, [sensor(1)], [relay(2), relay(3)]),
	], [ControllerPreset('SWK_1', HOST_ID, f'SWK_{HOST_ID}')]
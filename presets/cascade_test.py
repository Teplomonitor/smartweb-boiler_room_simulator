"""Isolated virtual I/O for cascade regression scenarios."""

from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import CascadeSettings, DhwSettings
from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc


def build_cascade_test(boiler_count):
	if boiler_count not in (2, 3, 4):
		raise ValueError('Cascade regression requires 2, 3 or 4 boilers')
	boiler_ids = tuple(range(103, 103 + boiler_count))
	def unmapped():
		return Mapping(0, 'CHANNEL_UNDEFINED', 0)
	programs = [
		ProgramPreset(snc.ProgramType.DHW, 'DEFAULT', 101, 'Cascade demand',
			DhwSettings(102), [Mapping(0, 'CHANNEL_SENSOR', 123)],
			[Mapping(0, 'CHANNEL_RELAY', 123)]),
		ProgramPreset(snc.ProgramType.CASCADE_MANAGER, 'DEFAULT', 102, 'Cascade regression',
			CascadeSettings(*boiler_ids), [Mapping(1, 'CHANNEL_SENSOR', 123), unmapped()], []),
	]
	controllers = [ControllerPreset('SWK_1', 123, 'Cascade sensors')]
	for index, boiler_id in enumerate(boiler_ids):
		host_id = 124 + index
		controllers.append(ControllerPreset('SWK_1', host_id, f'Boiler I/O {index + 1}'))
		programs.append(ProgramPreset(
			snc.ProgramType.BOILER, 'DEFAULT', boiler_id, f'Cascade boiler {index + 1}', None,
			[unmapped(), unmapped(), unmapped(), Mapping(0, 'CHANNEL_SENSOR', host_id)],
			[Mapping(0, 'CHANNEL_RELAY', host_id), unmapped(), unmapped(),
			 Mapping(1, 'CHANNEL_RELAY', host_id)],
		))
	return programs, controllers
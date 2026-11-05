"""Dedicated, destructive-on-load preset for embedded web mapping tests."""

import smartnet.constants as snc
from presets.preset import ProgramPreset


def get_presets_list():
	return [ProgramPreset(
		snc.ProgramType.DOUBLE_PUMP, 'DEFAULT', 101, 'Web binding test',
		None, [], [],
	)], []
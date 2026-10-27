"""Snowmelt firmware tests with a simulator-owned outdoor source."""

import smartnet.constants as snc
from presets.list.snowmelter import get_presets_list as get_real_presets
from presets.preset import ProgramPreset


def get_presets_list():
	programs, controllers = get_real_presets()
	return [
		ProgramPreset(program.get_type(), program.get_scheme(), program.get_id(),
			program.get_title(), None, [], [], execution='virtual')
		if program.get_type() == snc.ProgramType.OUTDOOR_SENSOR else program
		for program in programs
	], controllers
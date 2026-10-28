from presets.list.boiler_3_5_2 import get_presets_list as get_base_preset
from presets.preset import ProgramPreset
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


def get_presets_list():
	programs, controllers = get_base_preset()
	boiler = next(program for program in programs if program.get_type() == snc.ProgramType.BOILER)
	inputs = list(boiler.get_inputs())
	inputs.extend([None] * (4 - len(inputs)))
	inputs[3] = ChannelMapping(2, 'CHANNEL_SENSOR', controllers[0].get_id())
	boiler_with_error = ProgramPreset(
		boiler.get_type(), boiler.get_scheme(), boiler.get_id(),
		boiler.get_title(), boiler.getSettings(), inputs, boiler.get_outputs(),
	)
	return [boiler_with_error if program is boiler else program for program in programs], controllers
from presets.list.swimmingPool_with_level import get_presets_list as get_base_preset
from presets.preset import ProgramPreset
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


def get_presets_list():
	programs, controllers = get_base_preset()
	pool = next(program for program in programs if program.get_type() == snc.ProgramType.POOL)
	inputs = list(pool.get_inputs())
	inputs.extend([None] * (4 - len(inputs)))
	inputs[3] = ChannelMapping(3, 'CHANNEL_SENSOR', controllers[0].get_id())
	pool_with_flow = ProgramPreset(
		pool.get_type(), pool.get_scheme(), pool.get_id(),
		pool.get_title(), pool.getSettings(), inputs, pool.get_outputs(),
	)
	return [pool_with_flow if program is pool else program for program in programs], controllers
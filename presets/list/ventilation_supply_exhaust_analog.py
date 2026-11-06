from presets.ventilation import make_presets


def get_presets_list():
	return make_presets(supply_exhaust=True, analog=True)
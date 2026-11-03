from presets.list.district_heating_reserve import get_presets_list as reserve_presets
import smartnet.constants as snc


def get_presets_list():
	return reserve_presets(snc.DistrictHeatingReserveMode.SUPPLEMENT_AND_RESERVE)
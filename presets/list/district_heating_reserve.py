"""District heating with a common reserve valve signal and a city alarm input."""

from presets.list import district_heating_3_12_10 as base
from presets.preset import ProgramPreset
from presets.settings import DistrictHeatingSettings
import smartnet.constants as snc


def get_presets_list(reserve_mode=snc.DistrictHeatingReserveMode.RESERVE_ONLY):
	programs, controllers = base.get_presets_list()
	result = []
	for program in programs:
		if program.get_type() == snc.ProgramType.FILLING_LOOP:
			continue
		if program.get_type() != snc.ProgramType.DISTRICT_HEATING:
			result.append(program)
			continue
		inputs = list(program.get_inputs()) + [None, None, None,
			base.inputMapping(5, base.hostId['HOST_2'])]
		outputs = list(program.get_outputs()) + [base.outputMapping(7, base.hostId['HOST_2'])]
		settings = DistrictHeatingSettings(base.programId['BOILER'], reserve_mode=reserve_mode)
		result.append(ProgramPreset(program.get_type(), program.get_scheme(), program.get_id(),
			program.get_title(), settings, inputs, outputs))
	return result, controllers
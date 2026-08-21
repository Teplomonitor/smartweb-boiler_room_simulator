from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc

from presets.settings import HeatingCircuitSettings as heatingCircuitSettings
from presets.settings import DistrictHeatingSettings as dhSettings

import presets.preset


hostList = [
	'HOST_1',
	'HOST_2',
]

hostId = {
	'HOST_1': 123,
	'HOST_2': 124,
}

hostType = {
	'HOST_1': 'SWK_1',
	'HOST_2': 'SWK_1',
}

hostTitle = {
	'HOST_1': 'SWK_%d' % (hostId['HOST_1']),
	'HOST_2': 'SWK_%d' % (hostId['HOST_2']),
}

programList = [
	'DISTRICT_HEATING',
	'BOILER',
	'HEATING_CIRCUIT',
	'FILLING_LOOP',
]

programType = {
	'DISTRICT_HEATING': snc.ProgramType.DISTRICT_HEATING,
	'BOILER': snc.ProgramType.BOILER,
	'HEATING_CIRCUIT': snc.ProgramType.HEATING_CIRCUIT,
	'FILLING_LOOP': snc.ProgramType.FILLING_LOOP,
}

programScheme = {
	'DISTRICT_HEATING': 'DEFAULT',
	'BOILER': 'DEFAULT',
	'HEATING_CIRCUIT': 'CIRCUIT_MIXED',
	'FILLING_LOOP': 'DEFAULT',
}

programTitle = {
	'DISTRICT_HEATING': 'distHeat',
	'BOILER': 'Reserve',
	'HEATING_CIRCUIT': 'Test circuit',
	'FILLING_LOOP': 'Pressure',
}

programId = {
	'DISTRICT_HEATING': 108,
	'BOILER': 106,
	'HEATING_CIRCUIT': 105,
	'FILLING_LOOP': 109,
}

# The BOILER program here is only a dummy reserve/backup heat generator: it
# receives (or does not receive) the heat request that DistrictHeatingProgram
# sends to DistrictHeatingParameterId.PARAM_TEMPERATURE_SOURCE_ID. The
# 3.12.10.x scenarios only check TemperatureSourceParameterId.REQUIRED_TEMPERATURE
# and CURRENTLY_SERVICES_CONSUMER_ID on it, not its internal simulated
# behavior. Its temperature sensor and stage (burner) output are still mapped
# below: simulator/boiler.py treats an unmapped stage/pump output as
# permanently "on" (get_stage_state()/get_pump_state() default to 1 when
# is_mapped() is False), which made the boiler simulator behave as if it was
# constantly heating and settle its temperature around the collector's ~40 C
# backward temperature. Mapping the stage output lets it report its real
# (normally off) relay state instead.
programSettings = {
	'DISTRICT_HEATING': dhSettings(
		source=programId['BOILER'],
		alarm_program=programId['FILLING_LOOP'],
	),
	'BOILER': None,
	'HEATING_CIRCUIT': heatingCircuitSettings(
		source=programId['DISTRICT_HEATING'],
		heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
		requiredConstantFlowTemperature=45,
		temperatureCompensation=5,
	),
	'FILLING_LOOP': None,
}


def inputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)


def outputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_RELAY', host_id)


programInputs = {
	'DISTRICT_HEATING': [
		inputMapping(1, hostId['HOST_2']),
		inputMapping(2, hostId['HOST_2']),
		inputMapping(3, hostId['HOST_2']),
		inputMapping(4, hostId['HOST_2']),
	],
	'BOILER': [inputMapping(1, hostId['HOST_1'])],
	'HEATING_CIRCUIT': [inputMapping(4, hostId['HOST_1'])],
	'FILLING_LOOP': [inputMapping(5, hostId['HOST_2'])],
}

programOutputs = {
	'DISTRICT_HEATING': [
		outputMapping(2, hostId['HOST_2']),
		outputMapping(3, hostId['HOST_2']),
		None,
		outputMapping(6, hostId['HOST_2']),
	],
	'BOILER': [
		outputMapping(3, hostId['HOST_1']),
		outputMapping(2, hostId['HOST_1']),
	],
	'HEATING_CIRCUIT': [
		outputMapping(0, hostId['HOST_1']),
		None,
		None,
		outputMapping(1, hostId['HOST_1']),
	],
	'FILLING_LOOP': [],
}


def get_presets_list():
	programPresetList = []
	for prg in programList:
		programPresetList.append(presets.preset.ProgramPreset(
			programType[prg],
			programScheme[prg],
			programId[prg],
			programTitle[prg],
			programSettings[prg],
			programInputs[prg],
			programOutputs[prg],
		))

	controllerPresetList = []
	for ctrl in hostList:
		controllerPresetList.append(presets.preset.ControllerPreset(
			hostType[ctrl],
			hostId[ctrl],
			hostTitle[ctrl],
		))

	return programPresetList, controllerPresetList

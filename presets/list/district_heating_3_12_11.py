from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc

from presets.settings import HeatingCircuitSettings as hcSettings
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
	'HEATING_CIRCUIT',
	'OUTDOOR_SENSOR',
	'DISTRICT_HEATING',
	'FILLING_LOOP',
]

programType = {
	'HEATING_CIRCUIT': snc.ProgramType.HEATING_CIRCUIT,
	'OUTDOOR_SENSOR': snc.ProgramType.OUTDOOR_SENSOR,
	'DISTRICT_HEATING': snc.ProgramType.DISTRICT_HEATING,
	'FILLING_LOOP': snc.ProgramType.FILLING_LOOP,
}

programScheme = {
	'HEATING_CIRCUIT': 'CIRCUIT_MIXED',
	'OUTDOOR_SENSOR': 'DEFAULT',
	'DISTRICT_HEATING': 'DEFAULT',
	'FILLING_LOOP': 'DEFAULT',
}

programTitle = {
	'HEATING_CIRCUIT': 'Circ1',
	'OUTDOOR_SENSOR': 'OAT',
	'DISTRICT_HEATING': 'distHeat',
	'FILLING_LOOP': 'Pressure',
}

programId = {
	'HEATING_CIRCUIT': 101,
	'OUTDOOR_SENSOR': 107,
	'DISTRICT_HEATING': 108,
	'FILLING_LOOP': 109,
}

programSettings = {
	'HEATING_CIRCUIT': hcSettings(programId['DISTRICT_HEATING']),
	'OUTDOOR_SENSOR': None,
	'DISTRICT_HEATING': dhSettings(alarm_program=programId['FILLING_LOOP']),
	'FILLING_LOOP': None,
}


def inputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)


def outputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_RELAY', host_id)


programInputs = {
	'HEATING_CIRCUIT': [inputMapping(0, hostId['HOST_1'])],
	'OUTDOOR_SENSOR': [inputMapping(0, hostId['HOST_2'])],
	'DISTRICT_HEATING': [
		inputMapping(1, hostId['HOST_2']),
		inputMapping(2, hostId['HOST_2']),
		inputMapping(3, hostId['HOST_2']),
		inputMapping(4, hostId['HOST_2']),
	],
	'FILLING_LOOP': [inputMapping(5, hostId['HOST_2'])],
}

programOutputs = {
	'HEATING_CIRCUIT': [
		outputMapping(6, hostId['HOST_1']),
		None,
		None,
		outputMapping(0, hostId['HOST_1']),
	],
	'OUTDOOR_SENSOR': [],
	'DISTRICT_HEATING': [
		outputMapping(2, hostId['HOST_2']),
		outputMapping(3, hostId['HOST_2']),
		None,
		outputMapping(6, hostId['HOST_2']),
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

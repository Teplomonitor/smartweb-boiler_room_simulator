from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc

import presets.preset


hostList = [
	'HOST_1',
]

hostId = {
	'HOST_1': 123,
}

hostType = {
	'HOST_1': 'SWK_1',
}

hostTitle = {
	'HOST_1': 'SWK_%d' % hostId['HOST_1'],
}

programList = [
	'FILLING_LOOP',
]

programType = {
	'FILLING_LOOP': snc.ProgramType.FILLING_LOOP,
}

programScheme = {
	'FILLING_LOOP': 'DEFAULT',
}

programTitle = {
	'FILLING_LOOP': 'Filling loop',
}

programId = {
	'FILLING_LOOP': 101,
}

programSettings = {
	'FILLING_LOOP': None,
}


def inputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)


def outputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_RELAY', host_id)


programInputs = {
	'FILLING_LOOP': [inputMapping(0, hostId['HOST_1'])],
}

programOutputs = {
	'FILLING_LOOP': [
		outputMapping(0, hostId['HOST_1']),
		outputMapping(1, hostId['HOST_1']),
	],
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

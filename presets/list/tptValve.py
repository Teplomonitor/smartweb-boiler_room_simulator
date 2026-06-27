
from smartnet.channelMapping import ChannelMapping as Mapping

import presets.preset

hostList = [
	'HOST_1',
]

hostId = {
	'HOST_1' : 123,
}

hostType = {
	'HOST_1' : 'SWK_1',
}

hostTitle = {
	'HOST_1' : 'SWK_%d' % (hostId['HOST_1']),
}


programList = [
	'TPT_VALVE',
]

programType = {
	'TPT_VALVE': 'TPT_VALVE_ADAPTER',
}

programScheme = {
	'TPT_VALVE': 'DEFAULT',
}

programTitle = {
	'TPT_VALVE'     :'tpt-valve',
}

programId = {
	'TPT_VALVE': 101,
}

programSettings = {
	'TPT_VALVE': None,
}

def inputMapping (channel_id, host_id): return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)
def outputMapping(channel_id, host_id): return Mapping(channel_id, 'CHANNEL_RELAY' , host_id)


programInputs = {
	'TPT_VALVE'   : [inputMapping(0, hostId['HOST_1'])],
}

programOutputs = {
	'TPT_VALVE': [outputMapping(0, hostId['HOST_1']), outputMapping(1, hostId['HOST_1'])],
}

def get_presetsList() :
	programPresetList = []
	for prg in programList:
		programPresetList.append(presets.preset.ProgramPreset(
			programType    [prg],
			programScheme  [prg],
			programId      [prg],
			programTitle   [prg],
			programSettings[prg],
			programInputs  [prg],
			programOutputs [prg],
			)
		)

	controllerPresetList = []
	for ctrl in hostList:
		controllerPresetList.append(presets.preset.ControllerPreset(
			hostType    [ctrl],
			hostId      [ctrl],
			hostTitle   [ctrl],
			)
		)

	return programPresetList, controllerPresetList

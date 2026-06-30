from smartnet.channelMapping import ChannelMapping as Mapping

from presets.settings import SwimmingPoolSettings as spSettings

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
	'SWIMMING_POOL' ,
	'BOILER'        ,
]

programType = {
	'SWIMMING_POOL': 'POOL',
	'BOILER'       : 'BOILER',
}

programScheme = {
	'SWIMMING_POOL'   : 'DEFAULT',
	'BOILER'          : 'DEFAULT',
}

programTitle = {
	'SWIMMING_POOL'   :'Swimming pool',
	'BOILER'          :'Boiler1' ,
}

programId = {
	'SWIMMING_POOL'  : 101,
	'BOILER'         : 102,
}

programSettings = {
	'SWIMMING_POOL' : spSettings(programId['BOILER']),
	'BOILER'        : None,
}

def inputMapping (channel_id, host_id): return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)
def outputMapping(channel_id, host_id): return Mapping(channel_id, 'CHANNEL_RELAY' , host_id)


programInputs = {
	# Provide mapping for pool inputs so waterLevel (index 2) is bound
	'SWIMMING_POOL' : [
		inputMapping(0, hostId['HOST_1']),  # poolTemperature
		None,
#		inputMapping(1, hostId['HOST_1']),  # outsideRequest
		inputMapping(2, hostId['HOST_1']),  # waterLevel (needed by scenario)
		None,
#		inputMapping(3, hostId['HOST_1']),  # flow
	],
	'BOILER'        : [inputMapping(4, hostId['HOST_1'])],
}

programOutputs = {
	# Provide full mapping for pool outputs so waterLevelControl (index 2) is bound
	'SWIMMING_POOL' : [
		outputMapping(0, hostId['HOST_1']),  # circulationPump
		outputMapping(1, hostId['HOST_1']),  # loadingPump
		outputMapping(2, hostId['HOST_1']),  # waterLevelControl (needed by scenario)
	],
	'BOILER'        : [
		outputMapping(3, hostId['HOST_1']),
		outputMapping(4, hostId['HOST_1'])
	],
}

def get_presets_list() :
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


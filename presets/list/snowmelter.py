
from smartnet.channelMapping import ChannelMapping as Mapping
from presets.settings import SnowMelterSettings as smSettings

import presets.preset

hostList = [
	'HOST_1',
	'HOST_2',
]

hostId = {
	'HOST_1' : 123,
	'HOST_2' : 124,
}

hostType = {
	'HOST_1' : 'SWK_1',
	'HOST_2' : 'SWK_1',
}

hostTitle = {
	'HOST_1' : 'SWK_%d' % (hostId['HOST_1']),
	'HOST_2' : 'SWK_%d' % (hostId['HOST_2']),
}


programList = [
	'SNOW_MELTER'   ,
	'BOILER'        ,
	'OUTDOOR_SENSOR',
]

programType = {
	'SNOW_MELTER'    : 'SNOWMELT',
	'BOILER'         : 'BOILER'         ,
	'OUTDOOR_SENSOR' : 'OUTDOOR_SENSOR' ,
}

programScheme = {
	'SNOW_MELTER'     : 'DEFAULT',
	'BOILER'          : 'DEFAULT',
	'OUTDOOR_SENSOR'  : 'DEFAULT',
}

programTitle = {
	'SNOW_MELTER'     :'snowmelt',
	'BOILER'          :'Boiler1' ,
	'OUTDOOR_SENSOR'  :'OAT'     ,
}

programId = {
	'SNOW_MELTER'    : 101,
	'BOILER'         : 102,
	'OUTDOOR_SENSOR' : 103,
}

programSettings = {
	'SNOW_MELTER'   : smSettings(programId['BOILER']),
	'BOILER'        : None,
	'OUTDOOR_SENSOR': None,
}

def inputMapping (channel_id, host_id): return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)
def outputMapping(channel_id, host_id): return Mapping(channel_id, 'CHANNEL_RELAY' , host_id)

programInputs = {
	'SNOW_MELTER'   : [inputMapping(0, hostId['HOST_1']), inputMapping(1, hostId['HOST_1']), inputMapping(2, hostId['HOST_1'])],
	'BOILER'        : [inputMapping(3, hostId['HOST_1'])],
	'OUTDOOR_SENSOR': [inputMapping(4, hostId['HOST_1'])],
}

programOutputs = {
	'SNOW_MELTER'   : [None, outputMapping(1, hostId['HOST_1']), outputMapping(6, hostId['HOST_1'])],
	'BOILER'        : [outputMapping(3, hostId['HOST_1']), outputMapping(4, hostId['HOST_1'])],
	'OUTDOOR_SENSOR': [],
}

def getPresetsList() :
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

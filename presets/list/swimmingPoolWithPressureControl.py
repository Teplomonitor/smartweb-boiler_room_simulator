
from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc

from presets.settings import SwimmingPoolSettings as spSettings

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
	'SWIMMING_POOL' ,
	'BOILER'        ,
	'FILLING_LOOP'  ,
]

programType = {
	'SWIMMING_POOL': snc.ProgramType.POOL,
	'BOILER'       : snc.ProgramType.BOILER,
	'FILLING_LOOP' : snc.ProgramType.FILLING_LOOP,
}

programScheme = {
	'SWIMMING_POOL' : 'DEFAULT',
	'BOILER'        : 'DEFAULT',
	'FILLING_LOOP'  : 'DEFAULT',
}

programTitle = {
	'SWIMMING_POOL' : 'Swimming pool',
	'BOILER'        : 'Boiler1',
	'FILLING_LOOP'  : 'Pressure',
}

programId = {
	'SWIMMING_POOL' : 101,
	'BOILER'        : 102,
	'FILLING_LOOP'  : 103,
}

programSettings = {
	'SWIMMING_POOL' : spSettings(programId['BOILER']),
	'BOILER'        : None,
	'FILLING_LOOP'  : None,
}

def inputMapping (channel_id, host_id): return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)
def outputMapping(channel_id, host_id): return Mapping(channel_id, 'CHANNEL_RELAY' , host_id)


programInputs = {
	'SWIMMING_POOL' : [inputMapping(0, hostId['HOST_1'])],
	'BOILER'        : [inputMapping(4, hostId['HOST_1'])],
	'FILLING_LOOP'  : [inputMapping(0, hostId['HOST_2'])],
}

programOutputs = {
	'SWIMMING_POOL' : [
		outputMapping(0, hostId['HOST_1']),
		outputMapping(1, hostId['HOST_1'])
	],
	'BOILER'        : [
		outputMapping(3, hostId['HOST_1']),
		outputMapping(4, hostId['HOST_1'])
	],
	'FILLING_LOOP'  : [
		outputMapping(0, hostId['HOST_2']),
		outputMapping(1, hostId['HOST_2'])
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

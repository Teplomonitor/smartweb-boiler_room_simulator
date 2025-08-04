
from smartnet.channelMapping import ChannelMapping as Mapping

from presets.mapping import BoilerInputMapping          as boilerInputMapping
from presets.mapping import BoilerOutputMapping         as boilerOutputMapping
from presets.mapping import SwimmingPoolInputMapping    as spInputMapping
from presets.mapping import SwimmingPoolOutputMapping   as spOutputMapping

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
	'SWIMMING_POOL' : spInputMapping     (
		inputMapping(0, hostId['HOST_1'])
	),
	'BOILER'        : boilerInputMapping (inputMapping(4, hostId['HOST_1'])),
}

programOutputs = {
	'SWIMMING_POOL' : spOutputMapping(
		outputMapping(0, hostId['HOST_1']),
		outputMapping(1, hostId['HOST_1'])
	),
	'BOILER'        : boilerOutputMapping(
		pump    = outputMapping(3, hostId['HOST_1']),
		burner1 = outputMapping(4, hostId['HOST_1'])
	),
}

programPower = {
	'SWIMMING_POOL' :  2,
	'BOILER'        :  3,
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
			programPower   [prg],
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


from smartnet.channelMapping import ChannelMapping as Mapping

from presets.mapping import BoilerInputMapping          as boilerInputMapping
from presets.mapping import BoilerOutputMapping         as boilerOutputMapping
from presets.mapping import OatInputMapping             as oatInputMapping
from presets.mapping import OatOutputMapping            as oatOutputMapping
from presets.mapping import SnowMelterInputMapping      as smInputMapping
from presets.mapping import SnowMelterOutputMapping     as smOutputMapping
from presets.mapping import FillingLoopInputMapping     as flInputMapping
from presets.mapping import FillingLoopOutputMapping    as flOutputMapping

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
	'FILLING_LOOP'  ,
]

programType = {
	'SNOW_MELTER'    : 'SNOWMELT',
	'BOILER'         : 'BOILER'         ,
	'OUTDOOR_SENSOR' : 'OUTDOOR_SENSOR' ,
	'FILLING_LOOP'   : 'FILLING_LOOP' ,
}

programScheme = {
	'SNOW_MELTER'     : 'DEFAULT',
	'BOILER'          : 'DEFAULT',
	'OUTDOOR_SENSOR'  : 'DEFAULT',
	'FILLING_LOOP'    : 'DEFAULT',
}

programTitle = {
	'SNOW_MELTER'     :'snowmelt',
	'BOILER'          :'Boiler1' ,
	'OUTDOOR_SENSOR'  :'OAT'     ,
	'FILLING_LOOP'    :'Pressure',
}

programId = {
	'SNOW_MELTER'    : 101,
	'BOILER'         : 102,
	'OUTDOOR_SENSOR' : 103,
	'FILLING_LOOP'   : 104,
}

programSettings = {
	'SNOW_MELTER'   : smSettings(programId['BOILER']),
	'BOILER'        : None,
	'OUTDOOR_SENSOR': None,
	'FILLING_LOOP'  : None,
}

def inputMapping (channel_id, host_id): return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)
def outputMapping(channel_id, host_id): return Mapping(channel_id, 'CHANNEL_RELAY' , host_id)


programInputs = {
	'SNOW_MELTER'   : smInputMapping     (inputMapping(0, hostId['HOST_1']), inputMapping(1, hostId['HOST_1']), inputMapping(2, hostId['HOST_1'])),
	'BOILER'        : boilerInputMapping (inputMapping(3, hostId['HOST_1'])),
	'OUTDOOR_SENSOR': oatInputMapping    (inputMapping(4, hostId['HOST_1'])),
	'FILLING_LOOP'  : flInputMapping     (inputMapping(0, hostId['HOST_2'])),
}

programOutputs = {
	'SNOW_MELTER'   : smOutputMapping(None, outputMapping(1, hostId['HOST_1']), outputMapping(6, hostId['HOST_1'])),
	'BOILER'        : boilerOutputMapping(pump = outputMapping(3, hostId['HOST_1']), burner1 = outputMapping(4, hostId['HOST_1'])),
	'OUTDOOR_SENSOR': oatOutputMapping(),
	'FILLING_LOOP'  : flOutputMapping(outputMapping(0, hostId['HOST_2']), outputMapping(1, hostId['HOST_2'])),
}

programPower = {
	'SNOW_MELTER'   :  2,
	'BOILER'        :  3,
	'OUTDOOR_SENSOR': None,
	'FILLING_LOOP'  : None,
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

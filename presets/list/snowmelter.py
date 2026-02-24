
from presets.mapping import inputMapping  as inputMapping
from presets.mapping import outputMapping as outputMapping

from presets.mapping import BoilerInputMapping          as boilerInputMapping
from presets.mapping import BoilerOutputMapping         as boilerOutputMapping
from presets.mapping import OatInputMapping             as oatInputMapping
from presets.mapping import OatOutputMapping            as oatOutputMapping
from presets.mapping import SnowMelterInputMapping      as smInputMapping
from presets.mapping import SnowMelterOutputMapping     as smOutputMapping

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

programInputs = {
	'SNOW_MELTER'   : smInputMapping     (inputMapping(0, hostId['HOST_1']), inputMapping(1, hostId['HOST_1']), inputMapping(2, hostId['HOST_1'])),
	'BOILER'        : boilerInputMapping (inputMapping(3, hostId['HOST_1'])),
	'OUTDOOR_SENSOR': oatInputMapping    (inputMapping(4, hostId['HOST_1'])),
}

programOutputs = {
	'SNOW_MELTER'   : smOutputMapping(None, outputMapping(1, hostId['HOST_1']), outputMapping(6, hostId['HOST_1'])),
	'BOILER'        : boilerOutputMapping(pump = outputMapping(3, hostId['HOST_1']), burner1 = outputMapping(4, hostId['HOST_1'])),
	'OUTDOOR_SENSOR': oatOutputMapping(),
}

programPower = {
	'SNOW_MELTER'   :  2,
	'BOILER'        :  3,
	'OUTDOOR_SENSOR': None,
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

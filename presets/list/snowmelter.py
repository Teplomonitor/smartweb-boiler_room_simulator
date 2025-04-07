
from controllers.channelMapping import ChannelMapping as Mapping

from presets.mapping import BoilerInputMapping          as boilerInputMapping
from presets.mapping import BoilerOutputMapping         as boilerOutputMapping
from presets.mapping import OatInputMapping             as oatInputMapping
from presets.mapping import OatOutputMapping            as oatOutputMapping
from presets.mapping import SnowMelterInputMapping      as smInputMapping
from presets.mapping import SnowMelterOutputMapping     as smOutputMapping

from presets.settings import SnowMelterSettings as smSettings

import smartnet.constants as snc
import presets.preset

def getHostId():
	return 123

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

def inputMapping (channel_id): return Mapping(channel_id, 'CHANNEL_SENSOR', getHostId())
def outputMapping(channel_id): return Mapping(channel_id, 'CHANNEL_RELAY' , getHostId())


programInputs = {
	'SNOW_MELTER'   : smInputMapping     (inputMapping(0), inputMapping(1), inputMapping(2)),
	'BOILER'        : boilerInputMapping (inputMapping(3)),
	'OUTDOOR_SENSOR': oatInputMapping    (inputMapping(4)),
}

programOutputs = {
	'SNOW_MELTER'   : smOutputMapping(outputMapping(0), outputMapping(1), outputMapping(2)),
	'BOILER'        : boilerOutputMapping(pump = outputMapping(3), burner1 = outputMapping(4)),
	'OUTDOOR_SENSOR': oatOutputMapping(),
}

programPower = {
	'SNOW_MELTER'   :  2,
	'BOILER'        :  3,
	'OUTDOOR_SENSOR': None,
}

def getPresetsList() :
	presetList = []
	for prg in programList:
		presetList.append(presets.preset.ProgramPreset(
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

	return presetList

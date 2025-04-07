
from controllers.channelMapping import ChannelMapping as Mapping

from presets.mapping import HeatingCircuitInputMapping  as hcInputMapping
from presets.mapping import HeatingCircuitOutputMapping as hcOutputMapping
from presets.mapping import RoomInputMapping            as roomInputMapping
from presets.mapping import RoomOutputMapping           as roomOutputMapping
from presets.mapping import DhwInputMapping             as dhwInputMapping
from presets.mapping import DhwOutputMapping            as dhwOutputMapping
from presets.mapping import BoilerInputMapping          as boilerInputMapping
from presets.mapping import BoilerOutputMapping         as boilerOutputMapping
from presets.mapping import CascadeInputMapping         as cascadeInputMapping
from presets.mapping import CascadeOutputMapping        as cascadeOutputMapping
from presets.mapping import OatInputMapping             as oatInputMapping
from presets.mapping import OatOutputMapping            as oatOutputMapping
from presets.mapping import SnowMelterInputMapping      as smInputMapping
from presets.mapping import SnowMelterOutputMapping     as smOutputMapping

from presets.settings import HeatingCircuitSettings as hcSettings
from presets.settings import DhwSettings            as dhwSettings
from presets.settings import CascadeSettings        as cascadeSettings
from presets.settings import RoomSettings           as roomSettings
from presets.settings import SnowMelterSettings as smSettings

import presets.preset

def getHostId():
	return 123

programList = [
	'HEATING_CIRCUIT_1',
	'HEATING_CIRCUIT_2',
	'ROOM_DEVICE_1'    ,
	'ROOM_DEVICE_2'    ,
	'DHW'              ,
	'BOILER_1'         ,
	'BOILER_2'         ,
	'CASCADE_MANAGER'  ,
	'OUTDOOR_SENSOR'   ,
	'SNOW_MELTER'      ,
]

programType = {
	'HEATING_CIRCUIT_1' : 'HEATING_CIRCUIT',
	'HEATING_CIRCUIT_2' : 'HEATING_CIRCUIT',
	'ROOM_DEVICE_1'     : 'ROOM_DEVICE'    ,
	'ROOM_DEVICE_2'     : 'ROOM_DEVICE'    ,
	'DHW'               : 'DHW'            ,
	'BOILER_1'          : 'BOILER'         ,
	'BOILER_2'          : 'BOILER'         ,
	'CASCADE_MANAGER'   : 'CASCADE_MANAGER',
	'OUTDOOR_SENSOR'    : 'OUTDOOR_SENSOR' ,
	'SNOW_MELTER'       : 'SNOWMELT',
}

programScheme = {
	'HEATING_CIRCUIT_1' : 'CIRCUIT_MIXED' ,
	'HEATING_CIRCUIT_2' : 'CIRCUIT_MIXED',
	'ROOM_DEVICE_1'     : 'DEFAULT'       ,
	'ROOM_DEVICE_2'     : 'DEFAULT'       ,
	'DHW'               : 'DEFAULT'       ,
	'BOILER_1'          : 'DEFAULT'       ,
	'BOILER_2'          : 'DEFAULT'       ,
	'CASCADE_MANAGER'   : 'DEFAULT'       ,
	'OUTDOOR_SENSOR'    : 'DEFAULT'       ,
	'SNOW_MELTER'     : 'DEFAULT',
}

programTitle = {
	'HEATING_CIRCUIT_1' :'Circ1'   ,
	'HEATING_CIRCUIT_2' :'Circ2'   ,
	'ROOM_DEVICE_1'     :'Room1'   ,
	'ROOM_DEVICE_2'     :'Room2'   ,
	'DHW'               :'DHW'     ,
	'BOILER_1'          :'Boiler1' ,
	'BOILER_2'          :'Boiler2' ,
	'CASCADE_MANAGER'   :'Cascade' ,
	'OUTDOOR_SENSOR'    :'OAT'     ,
	'SNOW_MELTER'       :'snowmelt',
}

programId = {
	'HEATING_CIRCUIT_1' : 101,
	'HEATING_CIRCUIT_2' : 102,
	'ROOM_DEVICE_1'     : 103,
	'ROOM_DEVICE_2'     : 104,
	'DHW'               : 105,
	'BOILER_1'          : 106,
	'BOILER_2'          : 107,
	'CASCADE_MANAGER'   : 108,
	'OUTDOOR_SENSOR'    : 109,
	'SNOW_MELTER'       : 110,
}

programSettings = {
	'HEATING_CIRCUIT_1' : hcSettings(programId['CASCADE_MANAGER']),
	'HEATING_CIRCUIT_2' : hcSettings(programId['CASCADE_MANAGER'], 60),
	'ROOM_DEVICE_1'     : roomSettings(None                          , programId['HEATING_CIRCUIT_1']),
	'ROOM_DEVICE_2'     : roomSettings(programId['HEATING_CIRCUIT_2'], programId['HEATING_CIRCUIT_1']),
	'DHW'               : dhwSettings(programId['CASCADE_MANAGER']),
	'BOILER_1'          : None,
	'BOILER_2'          : None,
	'CASCADE_MANAGER'   : cascadeSettings(programId['BOILER_1'], programId['BOILER_2']),
	'OUTDOOR_SENSOR'    : None,
	'SNOW_MELTER'       : smSettings(programId['CASCADE_MANAGER']),
}

def inputMapping (channel_id): return Mapping(channel_id, 'CHANNEL_SENSOR', getHostId())
def outputMapping(channel_id): return Mapping(channel_id, 'CHANNEL_RELAY' , getHostId())


programInputs = {
	'HEATING_CIRCUIT_1' : hcInputMapping     (inputMapping(0)),
	'HEATING_CIRCUIT_2' : hcInputMapping     (inputMapping(1)),
	'ROOM_DEVICE_1'     : roomInputMapping   (inputMapping(2)),
	'ROOM_DEVICE_2'     : roomInputMapping   (inputMapping(3)),
	'DHW'               : dhwInputMapping    (inputMapping(4)),
	'BOILER_1'          : boilerInputMapping (),
	'BOILER_2'          : boilerInputMapping (),
	'CASCADE_MANAGER'   : cascadeInputMapping(inputMapping(6)),
	'OUTDOOR_SENSOR'    : oatInputMapping    (inputMapping(7)),
	'SNOW_MELTER'       : smInputMapping     (inputMapping(8), inputMapping(9), inputMapping(10)),
}

programOutputs = {
	'HEATING_CIRCUIT_1' : hcOutputMapping(analogValve = outputMapping(0), pump = outputMapping(1)),
	'HEATING_CIRCUIT_2' : hcOutputMapping(analogValve = outputMapping(2), pump = outputMapping(3)),
	'ROOM_DEVICE_1'     : roomOutputMapping(),
	'ROOM_DEVICE_2'     : roomOutputMapping(),
	'DHW'               : dhwOutputMapping(outputMapping(4), outputMapping(5)),
	'BOILER_1'          : boilerOutputMapping(pump = outputMapping(6), burner1 = outputMapping(7)),
	'BOILER_2'          : boilerOutputMapping(pump = outputMapping(8), burner1 = outputMapping(9)),
	'CASCADE_MANAGER'   : cascadeOutputMapping(),
	'OUTDOOR_SENSOR'    : oatOutputMapping(),
	'SNOW_MELTER'       : smOutputMapping(outputMapping(10), outputMapping(11), outputMapping(12)),
}

programPower = {
	'HEATING_CIRCUIT_1' : -2,
	'HEATING_CIRCUIT_2' : -3,
	'ROOM_DEVICE_1'     : -1,
	'ROOM_DEVICE_2'     : -2,
	'DHW'               : -4,
	'BOILER_1'          :  7,
	'BOILER_2'          :  7,
	'CASCADE_MANAGER'   :  0,
	'OUTDOOR_SENSOR'    : None,
	'SNOW_MELTER'       : -4,
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

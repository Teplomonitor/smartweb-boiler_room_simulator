
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

from presets.settings import HeatingCircuitSettings as hcSettings
from presets.settings import DhwSettings            as dhwSettings
from presets.settings import CascadeSettings        as cascadeSettings

import smartnet.constants as snc
import presets.preset

def getHostId():
	return 123

programList = [
	'HEATING_CIRCUIT_1',
	'HEATING_CIRCUIT_2',
	'ROOM_DEVICE_1'    ,
	'ROOM_DEVICE_2'    ,
	'DHW'              ,
	'BOILER'           ,
	'CASCADE_MANAGER'  ,
	'OUTDOOR_SENSOR'   ,
]

programType = {
	'HEATING_CIRCUIT_1' : snc.ProgramType['HEATING_CIRCUIT'],
	'HEATING_CIRCUIT_2' : snc.ProgramType['HEATING_CIRCUIT'],
	'ROOM_DEVICE_1'     : snc.ProgramType['ROOM_DEVICE'    ],
	'ROOM_DEVICE_2'     : snc.ProgramType['ROOM_DEVICE'    ],
	'DHW'               : snc.ProgramType['DHW'            ],
	'BOILER'            : snc.ProgramType['BOILER'         ],
	'CASCADE_MANAGER'   : snc.ProgramType['CASCADE_MANAGER'],
	'OUTDOOR_SENSOR'    : snc.ProgramType['OUTDOOR_SENSOR' ],
}

programScheme = {
	'HEATING_CIRCUIT_1' : snc.ProgramScheme['CIRCUIT_MIXED' ],
	'HEATING_CIRCUIT_2' : snc.ProgramScheme['CIRCUIT_DIRECT'],
	'ROOM_DEVICE_1'     : snc.ProgramScheme['DEFAULT'       ],
	'ROOM_DEVICE_2'     : snc.ProgramScheme['DEFAULT'       ],
	'DHW'               : snc.ProgramScheme['DEFAULT'       ],
	'BOILER'            : snc.ProgramScheme['DEFAULT'       ],
	'CASCADE_MANAGER'   : snc.ProgramScheme['DEFAULT'       ],
	'OUTDOOR_SENSOR'    : snc.ProgramScheme['DEFAULT'       ],
}

programTitle = {
	'HEATING_CIRCUIT_1' :'Circ1'   ,
	'HEATING_CIRCUIT_2' :'Circ2'   ,
	'ROOM_DEVICE_1'     :'Room1'   ,
	'ROOM_DEVICE_2'     :'Room2'   ,
	'DHW'               :'DHW'     ,
	'BOILER'            :'Boiler1' ,
	'CASCADE_MANAGER'   :'Cascade' ,
	'OUTDOOR_SENSOR'    :'OAT'     ,
}

programId = {
	'HEATING_CIRCUIT_1' : 101,
	'HEATING_CIRCUIT_2' : 102,
	'ROOM_DEVICE_1'     : 103,
	'ROOM_DEVICE_2'     : 104,
	'DHW'               : 105,
	'BOILER'            : 106,
	'CASCADE_MANAGER'   : 107,
	'OUTDOOR_SENSOR'    : 108,
}

programSettings = {
	'HEATING_CIRCUIT_1' : hcSettings(programId['CASCADE_MANAGER']),
	'HEATING_CIRCUIT_2' : hcSettings(programId['CASCADE_MANAGER']),
	'ROOM_DEVICE_1'     : None,
	'ROOM_DEVICE_2'     : None,
	'DHW'               : dhwSettings(programId['CASCADE_MANAGER']),
	'BOILER'            : None,
	'CASCADE_MANAGER'   : cascadeSettings(programId['BOILER']),
	'OUTDOOR_SENSOR'    : None,
}

def inputMapping (id): return Mapping(id, 'CHANNEL_SENSOR', getHostId())
def outputMapping(id): return Mapping(id, 'CHANNEL_RELAY' , getHostId())


programInputs = {
	'HEATING_CIRCUIT_1' : hcInputMapping     (inputMapping(0)).get(),
	'HEATING_CIRCUIT_2' : hcInputMapping     (inputMapping(1)).get(),
	'ROOM_DEVICE_1'     : roomInputMapping   (inputMapping(2)).get(),
	'ROOM_DEVICE_2'     : roomInputMapping   (inputMapping(3)).get(),
	'DHW'               : dhwInputMapping    (inputMapping(4)).get(),
	'BOILER'            : boilerInputMapping (inputMapping(5)).get(),
	'CASCADE_MANAGER'   : cascadeInputMapping(inputMapping(6)).get(),
	'OUTDOOR_SENSOR'    : oatInputMapping    (inputMapping(7)).get(),
}

programOutputs = {
	'HEATING_CIRCUIT_1' : hcOutputMapping(analogValve = outputMapping(0), pump = outputMapping(1)).get(),
	'HEATING_CIRCUIT_2' : hcOutputMapping(analogValve = outputMapping(2), pump = outputMapping(3)).get(),
	'ROOM_DEVICE_1'     : roomOutputMapping().get(),
	'ROOM_DEVICE_2'     : roomOutputMapping().get(),
	'DHW'               : dhwOutputMapping(outputMapping(4), outputMapping(5)).get(),
	'BOILER'            : boilerOutputMapping(pump = outputMapping(6), burner1 = outputMapping(7)).get(),
	'CASCADE_MANAGER'   : cascadeOutputMapping().get(),
	'OUTDOOR_SENSOR'    : oatOutputMapping().get(),
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
			programOutputs [prg]
			)
		)

	return presetList

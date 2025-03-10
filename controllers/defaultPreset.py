
from controllers.channelMapping import ChannelMapping as Mapping
from controllers.presetMapping import HeatingCircuitInputMapping  as hcInputMapping
from controllers.presetMapping import HeatingCircuitOutputMapping as hcOutputMapping
from controllers.presetMapping import RoomInputMapping  as roomInputMapping
from controllers.presetMapping import RoomOutputMapping as roomOutputMapping

import smartnet.constants as snc
import controllers.preset

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
	'HEATING_CIRCUIT_1' : {},
	'HEATING_CIRCUIT_2' : {},
	'ROOM_DEVICE_1'     : {},
	'ROOM_DEVICE_2'     : {},
	'DHW'               : {},
	'BOILER'            : None,
	'CASCADE_MANAGER'   : {},
	'OUTDOOR_SENSOR'    : None,
}

def inputMapping (id): return Mapping(id, 'CHANNEL_SENSOR', getHostId())
def outputMapping(id): return Mapping(id, 'CHANNEL_RELAY' , getHostId())


programInputs = {
	'HEATING_CIRCUIT_1' : hcInputMapping(temperature = inputMapping(0)).get(),
	'HEATING_CIRCUIT_2' : hcInputMapping(temperature = inputMapping(1)).get(),
	'ROOM_DEVICE_1'     : roomInputMapping(roomTemperature = inputMapping(2)).get(),
	'ROOM_DEVICE_2'     : roomInputMapping(roomTemperature = inputMapping(3)).get(),
	'DHW'               : hcInputMapping(temperature = inputMapping(4)).get(),
	'BOILER'            : None,
	'CASCADE_MANAGER'   : hcInputMapping(temperature = inputMapping(6)).get(),
	'OUTDOOR_SENSOR'    : hcInputMapping(temperature = inputMapping(7)).get(),
}

programOutputs = {
	'HEATING_CIRCUIT_1' : hcOutputMapping(analogValve = outputMapping(0), pump = outputMapping(1)).get(),
	'HEATING_CIRCUIT_2' : hcOutputMapping(analogValve = outputMapping(2), pump = outputMapping(3)).get(),
	'ROOM_DEVICE_1'     : None,
	'ROOM_DEVICE_2'     : None,
	'DHW'               : [outputMapping(4)],
	'BOILER'            : [outputMapping(5)],
	'CASCADE_MANAGER'   : None,
	'OUTDOOR_SENSOR'    : None,
}

def getPresetsList() :
	presetList = []
	for prg in programList:
		presetList.append(controllers.preset.ProgramPreset(
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

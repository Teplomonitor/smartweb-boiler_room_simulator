
from controllers.channelMapping import ChannelMapping as Mapping

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
	'HEATING_CIRCUIT_1' : 'HEATING_CIRCUIT',
	'HEATING_CIRCUIT_2' : 'HEATING_CIRCUIT',
	'ROOM_DEVICE_1'     : 'ROOM_DEVICE'    ,
	'ROOM_DEVICE_2'     : 'ROOM_DEVICE'    ,
	'DHW'               : 'DHW'            ,
	'BOILER'            : 'BOILER'         ,
	'CASCADE_MANAGER'   : 'CASCADE_MANAGER',
	'OUTDOOR_SENSOR'    : 'OUTDOOR_SENSOR' ,
}

programScheme = {
	'HEATING_CIRCUIT_1' : 'SCHEME_MIXED' ,
	'HEATING_CIRCUIT_2' : 'SCHEME_DIRECT',
	'ROOM_DEVICE_1'     : 'DEFAULT'      ,
	'ROOM_DEVICE_2'     : 'DEFAULT'      ,
	'DHW'               : 'DEFAULT'      ,
	'BOILER'            : 'DEFAULT'      ,
	'CASCADE_MANAGER'   : 'DEFAULT'      ,
	'OUTDOOR_SENSOR'    : 'DEFAULT'      ,
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

programInputs = {
	'HEATING_CIRCUIT_1' : [Mapping(0, 'CHANNEL_SENSOR', getHostId())],
	'HEATING_CIRCUIT_2' : [Mapping(1, 'CHANNEL_SENSOR', getHostId())],
	'ROOM_DEVICE_1'     : [Mapping(2, 'CHANNEL_SENSOR', getHostId())],
	'ROOM_DEVICE_2'     : [Mapping(3, 'CHANNEL_SENSOR', getHostId())],
	'DHW'               : [Mapping(4, 'CHANNEL_SENSOR', getHostId())],
	'BOILER'            : None,
	'CASCADE_MANAGER'   : [Mapping(6, 'CHANNEL_SENSOR', getHostId())],
	'OUTDOOR_SENSOR'    : [Mapping(7, 'CHANNEL_SENSOR', getHostId())],
}

programOutputs = {
	'HEATING_CIRCUIT_1' : [Mapping(0, 'CHANNEL_RELAY', getHostId())],
	'HEATING_CIRCUIT_2' : [Mapping(1, 'CHANNEL_RELAY', getHostId())],
	'ROOM_DEVICE_1'     : None,
	'ROOM_DEVICE_2'     : None,
	'DHW'               : [Mapping(4, 'CHANNEL_RELAY', getHostId())],
	'BOILER'            : [Mapping(5, 'CHANNEL_RELAY', getHostId())],
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

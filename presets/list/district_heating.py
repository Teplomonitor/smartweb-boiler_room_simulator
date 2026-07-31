
from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc

from presets.settings import HeatingCircuitSettings  as hcSettings
from presets.settings import DhwSettings             as dhwSettings
from presets.settings import RoomSettings            as roomSettings
from presets.settings import DistrictHeatingSettings as dhSettings

import presets.preset

def get_host_id():
	return 123

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
	'HEATING_CIRCUIT_1',
	'HEATING_CIRCUIT_2',
	'ROOM_DEVICE_1'    ,
	'ROOM_DEVICE_2'    ,
	'DHW'              ,
	'BOILER'           ,
	'OUTDOOR_SENSOR'   ,
	'DISTRICT_HEATING' ,
]

programType = {
	'HEATING_CIRCUIT_1' : snc.ProgramType.HEATING_CIRCUIT,
	'HEATING_CIRCUIT_2' : snc.ProgramType.HEATING_CIRCUIT,
	'ROOM_DEVICE_1'     : snc.ProgramType.ROOM_DEVICE    ,
	'ROOM_DEVICE_2'     : snc.ProgramType.ROOM_DEVICE    ,
	'DHW'               : snc.ProgramType.DHW            ,
	'BOILER'            : snc.ProgramType.BOILER         ,
	'OUTDOOR_SENSOR'    : snc.ProgramType.OUTDOOR_SENSOR ,
	'DISTRICT_HEATING'  : snc.ProgramType.DISTRICT_HEATING,
}

programScheme = {
	'HEATING_CIRCUIT_1' : 'CIRCUIT_MIXED' ,
	'HEATING_CIRCUIT_2' : 'CIRCUIT_MIXED' ,
	'ROOM_DEVICE_1'     : 'DEFAULT'       ,
	'ROOM_DEVICE_2'     : 'DEFAULT'       ,
	'DHW'               : 'DEFAULT'       ,
	'BOILER'            : 'DEFAULT'       ,
	'OUTDOOR_SENSOR'    : 'DEFAULT'       ,
	'DISTRICT_HEATING'  : 'DEFAULT'       ,
}

programTitle = {
	'HEATING_CIRCUIT_1' :'Circ1'   ,
	'HEATING_CIRCUIT_2' :'Circ2'   ,
	'ROOM_DEVICE_1'     :'Room1'   ,
	'ROOM_DEVICE_2'     :'Room2'   ,
	'DHW'               :'DHW'     ,
	'BOILER'            :'Boiler1' ,
	'OUTDOOR_SENSOR'    :'OAT'     ,
	'DISTRICT_HEATING'  :'distHeat',
}

programId = {
	'HEATING_CIRCUIT_1' : 101,
	'HEATING_CIRCUIT_2' : 102,
	'ROOM_DEVICE_1'     : 103,
	'ROOM_DEVICE_2'     : 104,
	'DHW'               : 105,
	'BOILER'            : 106,
	'OUTDOOR_SENSOR'    : 107,
	'DISTRICT_HEATING'  : 108,
}

programSettings = {
	'HEATING_CIRCUIT_1' : hcSettings(programId['DISTRICT_HEATING']),
	'HEATING_CIRCUIT_2' : hcSettings(programId['DISTRICT_HEATING'], 60),
	'ROOM_DEVICE_1'     : roomSettings(None                          , programId['HEATING_CIRCUIT_1']),
	'ROOM_DEVICE_2'     : roomSettings(programId['HEATING_CIRCUIT_2'], programId['HEATING_CIRCUIT_1']),
	'DHW'               : dhwSettings(programId['DISTRICT_HEATING']),
	'BOILER'            : None,
	'OUTDOOR_SENSOR'    : None,
	'DISTRICT_HEATING'  : dhSettings(programId['BOILER']),
}

def inputMapping (channel_id, host_id): return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)
def outputMapping(channel_id, host_id): return Mapping(channel_id, 'CHANNEL_RELAY' , host_id)


programInputs = {
	'HEATING_CIRCUIT_1' : [inputMapping(0, hostId['HOST_1'])],
	'HEATING_CIRCUIT_2' : [inputMapping(1, hostId['HOST_1'])],
	'ROOM_DEVICE_1'     : [inputMapping(2, hostId['HOST_1'])],
	'ROOM_DEVICE_2'     : [inputMapping(3, hostId['HOST_1'])],
	'DHW'               : [inputMapping(4, hostId['HOST_1'])],
	'BOILER'            : [inputMapping(5, hostId['HOST_1'])],
	'OUTDOOR_SENSOR'    : [inputMapping(0, hostId['HOST_2'])],
	'DISTRICT_HEATING'  : [
		inputMapping(1, hostId['HOST_2']),
		inputMapping(2, hostId['HOST_2']),
		inputMapping(3, hostId['HOST_2']),
		inputMapping(4, hostId['HOST_2']),
		],
}

programOutputs = {
	'HEATING_CIRCUIT_1' : [outputMapping(6, hostId['HOST_1']), None, None, outputMapping(0, hostId['HOST_1'])],
	'HEATING_CIRCUIT_2' : [outputMapping(7, hostId['HOST_1']), None, None, outputMapping(1, hostId['HOST_1'])],
	'ROOM_DEVICE_1'     : [],
	'ROOM_DEVICE_2'     : [],
	'DHW'               : [outputMapping(2, hostId['HOST_1']), outputMapping(3, hostId['HOST_1'])],
	'BOILER'            : [outputMapping(0, hostId['HOST_2']), outputMapping(1, hostId['HOST_2'])],
	'OUTDOOR_SENSOR'    : [],
	'DISTRICT_HEATING'  : [
		outputMapping(2, hostId['HOST_2']), 
		outputMapping(3, hostId['HOST_2']), 
		None, 
		outputMapping(6, hostId['HOST_2'])],
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

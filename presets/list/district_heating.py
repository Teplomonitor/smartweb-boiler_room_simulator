
from smartnet.channelMapping import ChannelMapping as Mapping

from presets.mapping import HeatingCircuitInputMapping   as hcInputMapping
from presets.mapping import HeatingCircuitOutputMapping  as hcOutputMapping
from presets.mapping import RoomInputMapping             as roomInputMapping
from presets.mapping import RoomOutputMapping            as roomOutputMapping
from presets.mapping import DhwInputMapping              as dhwInputMapping
from presets.mapping import DhwOutputMapping             as dhwOutputMapping
from presets.mapping import BoilerInputMapping           as boilerInputMapping
from presets.mapping import BoilerOutputMapping          as boilerOutputMapping
from presets.mapping import OatInputMapping              as oatInputMapping
from presets.mapping import OatOutputMapping             as oatOutputMapping
from presets.mapping import DistrictHeatingInputMapping  as dhInputMapping
from presets.mapping import DistrictHeatingOutputMapping as dhOutputMapping

from presets.settings import HeatingCircuitSettings  as hcSettings
from presets.settings import DhwSettings             as dhwSettings
from presets.settings import RoomSettings            as roomSettings
from presets.settings import DistrictHeatingSettings as dhSettings

import presets.preset

def getHostId():
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
	'HEATING_CIRCUIT_1' : 'HEATING_CIRCUIT',
	'HEATING_CIRCUIT_2' : 'HEATING_CIRCUIT',
	'ROOM_DEVICE_1'     : 'ROOM_DEVICE'    ,
	'ROOM_DEVICE_2'     : 'ROOM_DEVICE'    ,
	'DHW'               : 'DHW'            ,
	'BOILER'            : 'BOILER'         ,
	'OUTDOOR_SENSOR'    : 'OUTDOOR_SENSOR' ,
	'DISTRICT_HEATING'  : 'DISTRICT_HEATING',
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
	'HEATING_CIRCUIT_1' : hcInputMapping     (inputMapping(0, hostId['HOST_1'])),
	'HEATING_CIRCUIT_2' : hcInputMapping     (inputMapping(1, hostId['HOST_1'])),
	'ROOM_DEVICE_1'     : roomInputMapping   (inputMapping(2, hostId['HOST_1'])),
	'ROOM_DEVICE_2'     : roomInputMapping   (inputMapping(3, hostId['HOST_1'])),
	'DHW'               : dhwInputMapping    (inputMapping(4, hostId['HOST_1'])),
	'BOILER'            : boilerInputMapping (),
	'OUTDOOR_SENSOR'    : oatInputMapping    (inputMapping(0, hostId['HOST_2'])),
	'DISTRICT_HEATING'  : dhInputMapping     (
		inputMapping(1, hostId['HOST_2']),
		inputMapping(2, hostId['HOST_2']),
		inputMapping(3, hostId['HOST_2']),
		inputMapping(4, hostId['HOST_2']),
		),
}

programOutputs = {
	'HEATING_CIRCUIT_1' : hcOutputMapping(analogValve = outputMapping(6, hostId['HOST_1']), pump = outputMapping(0, hostId['HOST_1'])),
	'HEATING_CIRCUIT_2' : hcOutputMapping(analogValve = outputMapping(7, hostId['HOST_1']), pump = outputMapping(1, hostId['HOST_1'])),
	'ROOM_DEVICE_1'     : roomOutputMapping(),
	'ROOM_DEVICE_2'     : roomOutputMapping(),
	'DHW'               : dhwOutputMapping(outputMapping(2, hostId['HOST_1']), outputMapping(3, hostId['HOST_1'])),
	'BOILER'            : boilerOutputMapping(pump = outputMapping(0, hostId['HOST_2']), burner1 = outputMapping(1, hostId['HOST_2'])),
	'OUTDOOR_SENSOR'    : oatOutputMapping(),
	'DISTRICT_HEATING'  : dhOutputMapping(
		outputMapping(2, hostId['HOST_2']), 
		outputMapping(3, hostId['HOST_2']), 
		None, 
		outputMapping(6, hostId['HOST_2'])),
}

programPower = {
	'HEATING_CIRCUIT_1' : -2,
	'HEATING_CIRCUIT_2' : -3,
	'ROOM_DEVICE_1'     : -1,
	'ROOM_DEVICE_2'     : -2,
	'DHW'               : -4,
	'BOILER'            : 15,
	'OUTDOOR_SENSOR'    : None,
	'DISTRICT_HEATING'  :  7,
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


from smartnet.channelMapping import ChannelMapping as Mapping

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
from presets.settings import RoomSettings           as roomSettings

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
	'HEATING_CIRCUIT_1',
	'HEATING_CIRCUIT_2',
	'ROOM_DEVICE_1'    ,
	'ROOM_DEVICE_2'    ,
	'DHW'              ,
	'BOILER_1'         ,
	'BOILER_2'         ,
	'CASCADE_MANAGER'  ,
	'OUTDOOR_SENSOR'   ,
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
}

def inputMapping (channel_id, host_id): return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)
def outputMapping(channel_id, host_id): return Mapping(channel_id, 'CHANNEL_RELAY' , host_id)


programInputs = {
	'HEATING_CIRCUIT_1' : hcInputMapping     (inputMapping(0, hostId['HOST_1'])),
	'HEATING_CIRCUIT_2' : hcInputMapping     (inputMapping(1, hostId['HOST_1'])),
	'ROOM_DEVICE_1'     : roomInputMapping   (inputMapping(2, hostId['HOST_1'])),
	'ROOM_DEVICE_2'     : roomInputMapping   (inputMapping(3, hostId['HOST_1'])),
	'DHW'               : dhwInputMapping    (inputMapping(4, hostId['HOST_1'])),
	'BOILER_1'          : boilerInputMapping (),
	'BOILER_2'          : boilerInputMapping (),
	'CASCADE_MANAGER'   : cascadeInputMapping(inputMapping(0, hostId['HOST_2'])),
	'OUTDOOR_SENSOR'    : oatInputMapping    (inputMapping(1, hostId['HOST_2'])),
}

programOutputs = {
	'HEATING_CIRCUIT_1' : hcOutputMapping(analogValve = outputMapping(6, hostId['HOST_1']), pump = outputMapping(0, hostId['HOST_1'])),
	'HEATING_CIRCUIT_2' : hcOutputMapping(analogValve = outputMapping(7, hostId['HOST_1']), pump = outputMapping(1, hostId['HOST_1'])),
	'ROOM_DEVICE_1'     : roomOutputMapping(),
	'ROOM_DEVICE_2'     : roomOutputMapping(),
	'DHW'               : dhwOutputMapping(outputMapping(2, hostId['HOST_1']), outputMapping(3, hostId['HOST_1'])),
	'BOILER_1'          : boilerOutputMapping(pump = outputMapping(0, hostId['HOST_2']), burner1 = outputMapping(1, hostId['HOST_2'])),
	'BOILER_2'          : boilerOutputMapping(pump = outputMapping(2, hostId['HOST_2']), burner1 = outputMapping(3, hostId['HOST_2'])),
	'CASCADE_MANAGER'   : cascadeOutputMapping(),
	'OUTDOOR_SENSOR'    : oatOutputMapping(),
}

programPower = {
	'HEATING_CIRCUIT_1' : -2,
	'HEATING_CIRCUIT_2' : -3,
	'ROOM_DEVICE_1'     : -1,
	'ROOM_DEVICE_2'     : -2,
	'DHW'               : -4,
	'BOILER_1'          :  6,
	'BOILER_2'          :  6,
	'CASCADE_MANAGER'   :  0,
	'OUTDOOR_SENSOR'    : None,
}

def getPresetsList():
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


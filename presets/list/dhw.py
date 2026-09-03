from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc

from presets.settings import DhwSettings
import presets.preset

hostList = ['HOST_1', 'HOST_2']
hostId = {'HOST_1': 123, 'HOST_2': 124}
hostType = {'HOST_1': 'SWK_1', 'HOST_2': 'SWK_1'}
hostTitle = {
	'HOST_1': 'SWK_%d' % hostId['HOST_1'],
	'HOST_2': 'SWK_%d' % hostId['HOST_2'],
}

programList = ['DHW', 'BOILER', 'FILLING_LOOP']
programType = {
	'DHW': snc.ProgramType.DHW,
	'BOILER': snc.ProgramType.BOILER,
	'FILLING_LOOP': snc.ProgramType.FILLING_LOOP,
}
programScheme = {name: 'DEFAULT' for name in programList}
programTitle = {
	'DHW': 'DHW',
	'BOILER': 'Boiler1',
	'FILLING_LOOP': 'Filling loop',
}
programId = {'DHW': 101, 'BOILER': 102, 'FILLING_LOOP': 103}
programSettings = {
	'DHW': DhwSettings(programId['BOILER'], programId['FILLING_LOOP']),
	'BOILER': None,
	'FILLING_LOOP': None,
}


def inputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)


def outputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_RELAY', host_id)


programInputs = {
	'DHW': [inputMapping(0, hostId['HOST_1'])],
	'BOILER': [],
	'FILLING_LOOP': [inputMapping(0, hostId['HOST_2'])],
}
programOutputs = {
	'DHW': [outputMapping(2, hostId['HOST_1']), outputMapping(3, hostId['HOST_1'])],
	'BOILER': [outputMapping(2, hostId['HOST_2']), outputMapping(3, hostId['HOST_2'])],
	'FILLING_LOOP': [outputMapping(0, hostId['HOST_2']), outputMapping(1, hostId['HOST_2'])],
}


def get_presets_list():
	programPresetList = []
	for prg in programList:
		programPresetList.append(presets.preset.ProgramPreset(
			programType[prg], programScheme[prg], programId[prg], programTitle[prg],
			programSettings[prg], programInputs[prg], programOutputs[prg],
		))

	controllerPresetList = []
	for ctrl in hostList:
		controllerPresetList.append(presets.preset.ControllerPreset(
			hostType[ctrl], hostId[ctrl], hostTitle[ctrl],
		))
	return programPresetList, controllerPresetList

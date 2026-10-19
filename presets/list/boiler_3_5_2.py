from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc

from presets.settings import DhwSettings
import presets.preset


hostList = ['HOST_1']
hostId = {'HOST_1': 123}
hostType = {'HOST_1': 'SWK_1'}
hostTitle = {'HOST_1': 'SWK_123'}

programList = ['DHW', 'BOILER']
programType = {
	'DHW': snc.ProgramType.DHW,
	'BOILER': snc.ProgramType.BOILER,
}
programScheme = {name: 'DEFAULT' for name in programList}
programTitle = {
	'DHW': 'DHW test consumer',
	'BOILER': 'Boiler test',
}
programId = {'DHW': 101, 'BOILER': 102}
programSettings = {
	'DHW': DhwSettings(programId['BOILER']),
	'BOILER': None,
}


def inputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)


def outputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_RELAY', host_id)


programInputs = {
	'DHW': [inputMapping(0, hostId['HOST_1'])],
	'BOILER': [inputMapping(1, hostId['HOST_1'])],
}
programOutputs = {
	'DHW': [outputMapping(0, hostId['HOST_1'])],
	'BOILER': [None, outputMapping(1, hostId['HOST_1'])],
}


def get_presets_list():
	programPresetList = []
	for program in programList:
		programPresetList.append(presets.preset.ProgramPreset(
			programType[program],
			programScheme[program],
			programId[program],
			programTitle[program],
			programSettings[program],
			programInputs[program],
			programOutputs[program],
		))

	controllerPresetList = [
		presets.preset.ControllerPreset(
			hostType['HOST_1'],
			hostId['HOST_1'],
			hostTitle['HOST_1'],
		)
	]
	return programPresetList, controllerPresetList

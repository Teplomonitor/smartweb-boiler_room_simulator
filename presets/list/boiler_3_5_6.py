from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter

from presets.settings import DefaultSettings, DhwSettings
import presets.preset


hostList = ['HOST_1', 'HOST_2']
hostId = {'HOST_1': 123, 'HOST_2': 124}
hostType = {name: 'SWK_1' for name in hostList}
hostTitle = {name: f'SWK_{hostId[name]}' for name in hostList}

programList = ['DHW', 'BOILER', 'FILLING_LOOP']
programType = {
	'DHW': snc.ProgramType.DHW,
	'BOILER': snc.ProgramType.BOILER,
	'FILLING_LOOP': snc.ProgramType.FILLING_LOOP,
}
programScheme = {name: 'DEFAULT' for name in programList}
programTitle = {
	'DHW': 'DHW test consumer',
	'BOILER': 'Boiler alarm test',
	'FILLING_LOOP': 'Filling loop alarm source',
}
programId = {'DHW': 101, 'BOILER': 102, 'FILLING_LOOP': 103}
programSettings = {
	# Keep the consumer requesting heat even when the boiler receives an alarm.
	'DHW': DhwSettings(programId['BOILER']),
	'BOILER': DefaultSettings([
		RemoteControlParameter(
			snc.ProgramType.TEMPERATURE_SOURCE,
			snc.TemperatureSourceParameterId.ALARM_PROGRAM_ID,
			programId['FILLING_LOOP'],
		),
	]),
	'FILLING_LOOP': None,
}


def inputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_SENSOR', host_id)


def outputMapping(channel_id, host_id):
	return Mapping(channel_id, 'CHANNEL_RELAY', host_id)


programInputs = {
	'DHW': [inputMapping(0, hostId['HOST_1'])],
	'BOILER': [inputMapping(1, hostId['HOST_1'])],
	'FILLING_LOOP': [inputMapping(0, hostId['HOST_2'])],
}
programOutputs = {
	'DHW': [outputMapping(0, hostId['HOST_1'])],
	'BOILER': [
		outputMapping(1, hostId['HOST_1']),  # Pump
		outputMapping(2, hostId['HOST_1']),  # Stage 1
		outputMapping(3, hostId['HOST_1']),  # Stage 2
	],
	'FILLING_LOOP': [
		outputMapping(0, hostId['HOST_2']),
		outputMapping(1, hostId['HOST_2']),
	],
}


def get_presets_list():
	program_presets = [
		presets.preset.ProgramPreset(
			programType[name], programScheme[name], programId[name], programTitle[name],
			programSettings[name], programInputs[name], programOutputs[name],
		)
		for name in programList
	]
	controller_presets = [
		presets.preset.ControllerPreset(hostType[name], hostId[name], hostTitle[name])
		for name in hostList
	]
	return program_presets, controller_presets
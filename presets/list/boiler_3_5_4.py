from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc

from presets.settings import HeatingCircuitSettings as HeatingCircuitSettings
import presets.preset


HOST_ID = 123

PROGRAM_LIST = ['HEATING_CIRCUIT_1', 'HEATING_CIRCUIT_2', 'BOILER']
PROGRAM_TYPE = {
	'HEATING_CIRCUIT_1': snc.ProgramType.HEATING_CIRCUIT,
	'HEATING_CIRCUIT_2': snc.ProgramType.HEATING_CIRCUIT,
	'BOILER': snc.ProgramType.BOILER,
}
PROGRAM_SCHEME = {
	'HEATING_CIRCUIT_1': 'CIRCUIT_MIXED',
	'HEATING_CIRCUIT_2': 'CIRCUIT_MIXED',
	'BOILER': 'DEFAULT',
}
PROGRAM_TITLE = {
	'HEATING_CIRCUIT_1': 'Heating circuit 1 test',
	'HEATING_CIRCUIT_2': 'Heating circuit 2 test',
	'BOILER': 'Boiler 3.5.4 test',
}
PROGRAM_ID = {
	'HEATING_CIRCUIT_1': 101,
	'HEATING_CIRCUIT_2': 102,
	'BOILER': 103,
}
PROGRAM_SETTINGS = {
	'HEATING_CIRCUIT_1': HeatingCircuitSettings(
		PROGRAM_ID['BOILER'],
		heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
		requiredConstantFlowTemperature=35,
		temperatureCompensation=5,
	),
	'HEATING_CIRCUIT_2': HeatingCircuitSettings(
		PROGRAM_ID['BOILER'],
		heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
		requiredConstantFlowTemperature=45,
		temperatureCompensation=5,
	),
	'BOILER': None,
}


def input_mapping(channel_id):
	return Mapping(channel_id, 'CHANNEL_SENSOR', HOST_ID)


def output_mapping(channel_id):
	return Mapping(channel_id, 'CHANNEL_RELAY', HOST_ID)


PROGRAM_INPUTS = {
	'HEATING_CIRCUIT_1': [input_mapping(0)],
	'HEATING_CIRCUIT_2': [input_mapping(1)],
	'BOILER': [input_mapping(2)],
}
PROGRAM_OUTPUTS = {
	'HEATING_CIRCUIT_1': [output_mapping(0), None, None, output_mapping(1)],
	'HEATING_CIRCUIT_2': [output_mapping(2), None, None, output_mapping(3)],
	'BOILER': [output_mapping(4), output_mapping(5)],
}


def get_presets_list():
	program_preset_list = []
	for program in PROGRAM_LIST:
		program_preset_list.append(presets.preset.ProgramPreset(
			PROGRAM_TYPE[program],
			PROGRAM_SCHEME[program],
			PROGRAM_ID[program],
			PROGRAM_TITLE[program],
			PROGRAM_SETTINGS[program],
			PROGRAM_INPUTS[program],
			PROGRAM_OUTPUTS[program],
		))

	controller_preset_list = [
		presets.preset.ControllerPreset('SWK_1', HOST_ID, f'SWK_{HOST_ID}'),
	]
	return program_preset_list, controller_preset_list

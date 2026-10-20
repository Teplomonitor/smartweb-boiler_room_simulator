from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import DefaultSettings, HeatingCircuitSettings
from smartnet.channelMapping import ChannelMapping
from smartnet.remoteControl import RemoteControlParameter
import smartnet.constants as snc


HOST_ID = 123
CIRCUIT_ID = 101
BOILER_ID = 102


def input_mapping(channel_id):
	return ChannelMapping(channel_id, 'CHANNEL_SENSOR', HOST_ID)


def output_mapping(channel_id):
	# Virtual controller relays transport both discrete and 1..254 analog values.
	return ChannelMapping(channel_id, 'CHANNEL_RELAY', HOST_ID)


def get_presets_list():
	program_presets = [
		ProgramPreset(
			snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_MIXED', CIRCUIT_ID,
			'Boiler modulation test consumer',
			HeatingCircuitSettings(
				BOILER_ID,
				heatingSlope=1,
				heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
				requiredConstantFlowTemperature=45,
				temperatureCompensation=0,
			),
			[input_mapping(0), None, None, None, input_mapping(2)],
			[output_mapping(0), None, None, output_mapping(1)],
		),
		ProgramPreset(
			snc.ProgramType.BOILER, 'DEFAULT', BOILER_ID,
			'Boiler 3.5.7 analog power test',
			DefaultSettings([
				RemoteControlParameter(
					snc.ProgramType.TEMPERATURE_GENERATOR,
					snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE, 20,
				),
				RemoteControlParameter(
					snc.ProgramType.TEMPERATURE_GENERATOR,
					snc.TemperatureGeneratorParameterId.MAXIMUM_TEMPERATURE, 80,
				),
			]),
			[input_mapping(1)],
			[output_mapping(2), None, None, output_mapping(3)],
		),
	]
	return program_presets, [ControllerPreset('SWK_1', HOST_ID, f'SWK_{HOST_ID}')]
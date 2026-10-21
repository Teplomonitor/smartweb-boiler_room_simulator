from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import CascadeSettings, HeatingCircuitSettings
from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.constants as snc


HOST_ID = 123
CIRCUIT_IDS = (101, 102)
CASCADE_ID = 103
BOILER_IDS = (104, 105)


def sensor_mapping(channel_id):
	return Mapping(channel_id, 'CHANNEL_SENSOR', HOST_ID)


def relay_mapping(channel_id):
	return Mapping(channel_id, 'CHANNEL_RELAY', HOST_ID)


def unmapped_channel():
	return Mapping(0, 'CHANNEL_UNDEFINED', 0)


def get_presets_list():
	programs = []
	for index, circuit_id in enumerate(CIRCUIT_IDS):
		programs.append(ProgramPreset(
			snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_MIXED', circuit_id,
			f'Cascade test circuit {index + 1}',
			HeatingCircuitSettings(
				CASCADE_ID,
				heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
				requiredConstantFlowTemperature=40 + index * 10,
				temperatureCompensation=0,
			),
			[sensor_mapping(index)],
			[relay_mapping(index * 2), unmapped_channel(), unmapped_channel(), relay_mapping(index * 2 + 1)],
		))
	programs.append(ProgramPreset(
		snc.ProgramType.CASCADE_MANAGER, 'DEFAULT', CASCADE_ID, 'Cascade 3.6.4 test',
		CascadeSettings(*BOILER_IDS),
		[sensor_mapping(2), unmapped_channel()], [],
	))
	for index, boiler_id in enumerate(BOILER_IDS):
		programs.append(ProgramPreset(
			snc.ProgramType.BOILER, 'DEFAULT', boiler_id, f'Cascade boiler {index + 1}',
			None,
			# No local temperature control, external demand or alarm input.
			[unmapped_channel() for _ in range(4)],
			[relay_mapping(4 + index * 2), unmapped_channel(), unmapped_channel(), relay_mapping(5 + index * 2)],
		))
	return programs, [ControllerPreset('SWK_1', HOST_ID, 'SWK_123')]
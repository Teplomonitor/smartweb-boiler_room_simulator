from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import CascadeSettings, DhwSettings, HeatingCircuitSettings
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


HOST_ID = 123
HEATING_LINE_ID = 101
CIRCUIT_IDS = (102, 103)
DHW_ID = 104
CASCADE_ID = 105
BOILER_IDS = (106, 107)
OUTDOOR_ID = 108


def get_presets_list():
	def sensor(channel_id):
		return ChannelMapping(channel_id, 'CHANNEL_SENSOR', HOST_ID)

	def relay(channel_id):
		return ChannelMapping(channel_id, 'CHANNEL_RELAY', HOST_ID)

	def unmapped():
		return ChannelMapping(0, 'CHANNEL_UNDEFINED', 0)

	def circuit_settings(source, temperature):
		return HeatingCircuitSettings(
			source=source,
			heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
			requiredConstantFlowTemperature=temperature, temperatureCompensation=0,
		)

	# Scenario binding selects programs of the same type in preset order.
	programs = [ProgramPreset(
		snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_HEATING_LINE', HEATING_LINE_ID,
		'Heating line 3.3.6', circuit_settings(CASCADE_ID, 10),
		[sensor(0)], [unmapped(), unmapped(), unmapped(), relay(0)],
	)]
	for index, circuit_id in enumerate(CIRCUIT_IDS):
		programs.append(ProgramPreset(
			snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_DIRECT', circuit_id,
			f'Heating line consumer {index + 1}',
			circuit_settings(HEATING_LINE_ID, 40 + index * 10),
			[sensor(1 + index)], [unmapped(), unmapped(), unmapped(), relay(1 + index)],
		))
	programs.extend([
		ProgramPreset(
			snc.ProgramType.DHW, 'DEFAULT', DHW_ID, 'Heating line DHW',
			DhwSettings(HEATING_LINE_ID), [sensor(3)], [relay(3)],
		),
		ProgramPreset(
			snc.ProgramType.CASCADE_MANAGER, 'DEFAULT', CASCADE_ID, 'House cascade 3.3.6',
			CascadeSettings(*BOILER_IDS), [sensor(4), unmapped()], [],
		),
	])
	for index, boiler_id in enumerate(BOILER_IDS):
		programs.append(ProgramPreset(
			snc.ProgramType.BOILER, 'DEFAULT', boiler_id, f'House boiler {index + 1}',
			# Only cascade control: no local thermostat, external request or alarm.
			None, [unmapped() for _ in range(4)],
			[relay(4 + index * 2), unmapped(), unmapped(), relay(5 + index * 2)],
		))
	programs.append(ProgramPreset(
		snc.ProgramType.OUTDOOR_SENSOR, 'DEFAULT', OUTDOOR_ID, 'Outdoor 3.3.6',
		None, [sensor(5)], [],
	))
	return programs, [ControllerPreset('SWK_1', HOST_ID, 'SWK_123')]
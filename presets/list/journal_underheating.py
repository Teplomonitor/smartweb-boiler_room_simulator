from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import DhwSettings, HeatingCircuitSettings
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


HOST_ID = 123
CIRCUIT_ID = 101
DHW_ID = 102
BOILER_ID = 103


def get_presets_list():
	def sensor(index):
		return ChannelMapping(index, 'CHANNEL_SENSOR', HOST_ID)

	def relay(index):
		return ChannelMapping(index, 'CHANNEL_RELAY', HOST_ID)

	def unmapped():
		return ChannelMapping(0, 'CHANNEL_UNDEFINED', 0)

	programs = [
		ProgramPreset(
			snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_DIRECT', CIRCUIT_ID, 'Journal circuit',
			HeatingCircuitSettings(source=BOILER_ID,
				heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
				requiredConstantFlowTemperature=50, temperatureCompensation=0),
			[sensor(0)], [unmapped(), unmapped(), unmapped(), relay(0)],
		),
		ProgramPreset(snc.ProgramType.DHW, 'DEFAULT', DHW_ID, 'Journal DHW',
			DhwSettings(BOILER_ID), [sensor(1)], [relay(1)]),
		ProgramPreset(snc.ProgramType.BOILER, 'DEFAULT', BOILER_ID, 'Journal heat source',
			None, [sensor(2)], [relay(2), relay(3)]),
	]
	return programs, [ControllerPreset('SWK_1', HOST_ID, 'SWK_123')]
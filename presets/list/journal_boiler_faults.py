from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import HeatingCircuitSettings
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


HOST_ID = 123
CIRCUIT_ID = 101
BOILER_ID = 102


def get_presets_list():
	def sensor(index):
		return ChannelMapping(index, 'CHANNEL_SENSOR', HOST_ID)

	def relay(index):
		return ChannelMapping(index, 'CHANNEL_RELAY', HOST_ID)

	def unmapped():
		return ChannelMapping(0, 'CHANNEL_UNDEFINED', 0)

	programs = [
		ProgramPreset(snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_DIRECT', CIRCUIT_ID,
			'Journal boiler demand', HeatingCircuitSettings(source=BOILER_ID,
				heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
				requiredConstantFlowTemperature=70, temperatureCompensation=0),
			[sensor(0)], [unmapped(), unmapped(), unmapped(), relay(0)]),
		ProgramPreset(snc.ProgramType.BOILER, 'DEFAULT', BOILER_ID,
			'Journal boiler', None, [sensor(1), sensor(2)], [relay(1), relay(2)]),
	]
	return programs, [ControllerPreset('SWK_1', HOST_ID, 'SWK_123')]
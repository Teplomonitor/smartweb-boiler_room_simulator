from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc
from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import HeatingCircuitSettings


HOST_ID = 123
CIRCUIT_ID = 101
BOILER_ID = 102


def get_presets_list():
	def sensor(channel_id):
		return ChannelMapping(channel_id, 'CHANNEL_SENSOR', HOST_ID)

	def relay(channel_id):
		return ChannelMapping(channel_id, 'CHANNEL_RELAY', HOST_ID)

	programs = [
		ProgramPreset(
			snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_MIXED', CIRCUIT_ID,
			'Circuit 3.3.3', HeatingCircuitSettings(
				source=BOILER_ID,
				heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
				requiredConstantFlowTemperature=40,
				temperatureCompensation=5,
			),
			[sensor(0)],
			# No analog output: opening, closing and pump use separate relays.
			[None, relay(0), relay(1), relay(2)],
		),
		ProgramPreset(
			snc.ProgramType.BOILER, 'DEFAULT', BOILER_ID, 'Source 3.3.3',
			None, [sensor(1)],
			# No pump mapping: boiler simulator assumes permanent circulation.
			[None, relay(3)],
		),
	]
	return programs, [ControllerPreset('SWK_1', HOST_ID, f'SWK_{HOST_ID}')]

from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc
from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import HeatingCircuitSettings


HOST_ID = 123
BOILER_ID = 104


def get_presets_list():
	def sensor(channel_id):
		return ChannelMapping(channel_id, 'CHANNEL_SENSOR', HOST_ID)

	def relay(channel_id):
		return ChannelMapping(channel_id, 'CHANNEL_RELAY', HOST_ID)

	programs = [
		ProgramPreset(
			snc.ProgramType.HEATING_CIRCUIT, scheme, program_id, title,
			HeatingCircuitSettings(
				source=BOILER_ID,
				heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
				requiredConstantFlowTemperature=40, temperatureCompensation=0,
			),
			inputs, outputs,
		)
		for scheme, program_id, title, inputs, outputs in (
			('CIRCUIT_MIXED', 101, 'Mixed with sensor', [sensor(0)],
			 [relay(0), None, None, relay(1)]),
			('CIRCUIT_DIRECT', 102, 'Direct without sensor', [],
			 [None, None, None, relay(2)]),
			('CIRCUIT_MIXED', 103, 'Mixed without sensor', [],
			 [relay(3), None, None, relay(4)]),
		)
	]
	programs.append(ProgramPreset(
		snc.ProgramType.BOILER, 'DEFAULT', BOILER_ID, 'Priority source',
		None, [sensor(1)], [None, relay(5)],
	))
	return programs, [ControllerPreset('SWK_1', HOST_ID, f'SWK_{HOST_ID}')]
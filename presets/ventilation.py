"""Shared plant for the four automatically discovered ventilation presets."""

from presets.preset import ControllerPreset, ProgramPreset
from presets.settings import HeatingCircuitSettings, RoomSettings
from smartnet.channelMapping import ChannelMapping
import smartnet.constants as snc


ROOM_ID = 101
VENTILATION_ID = 102
CIRCUIT_ID = 103
BOILER_ID = 104
OUTDOOR_ID = 105


def make_presets(supply_exhaust=False, analog=True):
	def sensor(channel, host=123):
		return ChannelMapping(channel, 'CHANNEL_SENSOR', host)

	def relay(channel, host=123):
		return ChannelMapping(channel, 'CHANNEL_RELAY', host)

	outputs = [None] * 9
	outputs[6] = relay(4)  # Common fan enable, also used with analog speed.
	outputs[7] = relay(5) if analog else None
	outputs[8] = relay(6) if supply_exhaust else None
	if analog:
		outputs[0] = relay(0)
		outputs[1] = relay(1) if supply_exhaust else None
		outputs[2] = relay(2)
		outputs[3] = relay(3) if supply_exhaust else None
	else:
		outputs[4] = relay(2)
		outputs[5] = relay(3) if supply_exhaust else None
	programs = [
		ProgramPreset(snc.ProgramType.ROOM_DEVICE, 'DEFAULT', ROOM_ID, 'Комната',
			RoomSettings(source_1=0, source_2=0, source_3=CIRCUIT_ID,
				ventilation=VENTILATION_ID, required_humidity=45),
			[sensor(0), None, None, None, sensor(1)], []),
		ProgramPreset(snc.ProgramType.VENTILATION,
			'PROGRAM_SCHEME_1' if supply_exhaust else 'PROGRAM_SCHEME_0',
			VENTILATION_ID, 'Вентиляция', None,
			[sensor(0, 124) if supply_exhaust else None, sensor(0, 125), sensor(1, 125),
				sensor(1, 124) if supply_exhaust else None], outputs),
		ProgramPreset(snc.ProgramType.HEATING_CIRCUIT, 'CIRCUIT_MIXED', CIRCUIT_ID,
			'Контур калорифера', HeatingCircuitSettings(source=BOILER_ID,
				heatCalculationMode=snc.ConsumerHeatCalculationMode.CONSTANT_TEMPERATURE,
				requiredConstantFlowTemperature=40),
			[sensor(2), None, None, None, sensor(3)],
			[relay(0, 124), None, None, relay(1, 124)]),
		ProgramPreset(snc.ProgramType.BOILER, 'DEFAULT', BOILER_ID,
			'Котёл', None, [sensor(4)], [None, relay(2, 124)]),
		ProgramPreset(snc.ProgramType.OUTDOOR_SENSOR, 'DEFAULT', OUTDOOR_ID,
			'Улица', None, [sensor(5)], []),
	]
	controllers = [ControllerPreset('SWK_1', host, f'SWK_{host}') for host in (123, 124, 125)]
	return programs, controllers
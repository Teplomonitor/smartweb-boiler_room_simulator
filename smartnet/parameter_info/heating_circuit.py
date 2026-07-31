"""Metadata for HEATING_CIRCUIT parameters."""

from smartnet.constants import HeatingCircuitParameterId

PARAMETER_INFO = {
	HeatingCircuitParameterId.FROST_PROTECTION_TEMPERATURE: {'type': 'TEMPERATURE'},
	HeatingCircuitParameterId.VALVE_RUNING_TIME:             {'type': 'TIME_MS'},
	HeatingCircuitParameterId.VALVE_OPEN_PROPORTIONAL_BAND:  {'type': 'TEMPERATURE'},
	HeatingCircuitParameterId.VALVE_CLOSE_PROPORTIONAL_BAND: {'type': 'TEMPERATURE'},
	HeatingCircuitParameterId.VALVE_BLOCK:                   {'type': 'UINT8_T'},
	HeatingCircuitParameterId.PUMP_MODE:                     {'type': 'UINT8_T'},
	HeatingCircuitParameterId.PUMP_OFF_OUTDOOR_TEMPERATURE:  {'type': 'TEMPERATURE'},
	HeatingCircuitParameterId.ANALOG_CICRULATION_PUMP_STATE: {'type': 'UINT8_T'},
	HeatingCircuitParameterId.ANALOG_HEATCHANGE_PUMP_STATE:  {'type': 'UINT8_T'},
	HeatingCircuitParameterId.VALVE_POSITION:                {'type': 'UINT8_T'},
}

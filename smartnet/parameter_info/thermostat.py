"""Metadata for THERMOSTAT parameters, excluding channel pseudo-parameters."""

from smartnet.constants import ThermostatParameterId

PARAMETER_INFO = {
	ThermostatParameterId.REQUIRED_TEMPERATURE: {'type': 'TEMPERATURE'},
	ThermostatParameterId.REQUIRED_DELTA:       {'type': 'TEMPERATURE'},
	ThermostatParameterId.MODE:                 {'type': 'UINT8_T'},
	ThermostatParameterId.VALVE_NORMAL_STATE:   {'type': 'UINT8_T'},
	ThermostatParameterId.K_PROPORTIONAL:       {'type': 'TEMPERATURE'},
	ThermostatParameterId.K_INTEGRATION:        {'type': 'UINT8_T'},
	ThermostatParameterId.K_DIFFERENTIATION:    {'type': 'UINT8_T'},
	ThermostatParameterId.HISTERESIS:           {'type': 'TEMPERATURE'},
}

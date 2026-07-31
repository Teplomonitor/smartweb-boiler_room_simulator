"""Metadata for TEMPERATURE_SOURCE parameters, excluding channel pseudo-parameters."""

from smartnet.constants import TemperatureSourceParameterId

PARAMETER_INFO = {
	TemperatureSourceParameterId.REQUIRED_TEMPERATURE:             {'type': 'TEMPERATURE'},
	TemperatureSourceParameterId.WORK_TIME:                        {'type': 'UINT16_T'},
	TemperatureSourceParameterId.PRIORITY:                         {'type': 'UINT8_T'},
	TemperatureSourceParameterId.CURRENTLY_SERVICES_CONSUMER_ID:   {'type': 'UINT8_T'},
	TemperatureSourceParameterId.OUTSIDE_TEMPERATURE_REQUEST_VALUE: {'type': 'TEMPERATURE'},
	TemperatureSourceParameterId.ALARM_PROGRAM_ID:                 {'type': 'UINT8_T'},
	TemperatureSourceParameterId.ERROR_STATE:                      {'type': 'UINT8_T'},
}

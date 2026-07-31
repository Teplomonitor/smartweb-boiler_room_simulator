"""Metadata for CONSUMER parameters."""

from smartnet.constants import ConsumerParameterId

PARAMETER_INFO = {
	ConsumerParameterId.PRIORITY:                 {'type': 'UINT8_T'},
	ConsumerParameterId.GENERATOR_ID:             {'type': 'UINT8_T'},
	ConsumerParameterId.DUMMY1:                   {'type': 'UINT8_T'},
	ConsumerParameterId.DUMMY2:                   {'type': 'UINT8_T'},
	ConsumerParameterId.TEMPERATURE_COMPENSATION: {'type': 'TEMPERATURE'},
	ConsumerParameterId.REQUIRED_TEMPERATURE:     {'type': 'TEMPERATURE'},
	ConsumerParameterId.GENERATOR_TEMPERATURE:    {'type': 'TEMPERATURE'},
	ConsumerParameterId.HEAT_EXTRICATION_ENABLED: {'type': 'UINT8_T'},
	ConsumerParameterId.ALARM_PROGRAM_ID:         {'type': 'UINT8_T'},
}

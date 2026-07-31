"""Metadata for SNOWMELT parameters."""

from smartnet.constants import SnowMelterParameterId

PARAMETER_INFO = {
	SnowMelterParameterId.WORK_MODE:                                              {'type': 'UINT8_T'},
	SnowMelterParameterId.MINIMUM_OUTDOOR_TEMPERATURE:                            {'type': 'TEMPERATURE'},
	SnowMelterParameterId.MAXIMUM_OUTDOOR_TEMPERATURE:                            {'type': 'TEMPERATURE'},
	SnowMelterParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE_OF_SECONDARY_CIRCUIT: {'type': 'TEMPERATURE'},
	SnowMelterParameterId.OUTDOOR_TEMPERATURE:                                    {'type': 'TEMPERATURE'},
	SnowMelterParameterId.PRIMARY_CIRCUIT_PROTECTION_TEMPERATURE:                 {'type': 'TEMPERATURE'},
	SnowMelterParameterId.REQUIRED_PLATE_TEMPERATURE:                             {'type': 'TEMPERATURE'},
}

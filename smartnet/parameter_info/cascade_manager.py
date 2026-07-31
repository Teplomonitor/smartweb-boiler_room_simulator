"""Metadata for CASCADE_MANAGER parameters."""

from smartnet.constants import CascadeManagerParameterId
from .common import CASCADE_SOURCES_MAX_NUM, SCHEDULE_ARRAY_SIZE

PARAMETER_INFO = {
	CascadeManagerParameterId.PARAM_ROTATION_PERIOD:                       {'type': 'UINT8_T'},
	CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID:                 {'type': 'UINT8_T', 'array_size': CASCADE_SOURCES_MAX_NUM},
	CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_TYPE:               {'type': 'UINT8_T', 'array_size': CASCADE_SOURCES_MAX_NUM},
	CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_POWER:              {'type': 'UINT8_T', 'array_size': CASCADE_SOURCES_MAX_NUM},
	CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_WORKTIME:           {'type': 'UINT8_T', 'array_size': CASCADE_SOURCES_MAX_NUM},
	CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_PRIORITY:           {'type': 'UINT8_T', 'array_size': CASCADE_SOURCES_MAX_NUM},
	CascadeManagerParameterId.PARAM_P_FACTOR:                              {'type': 'UINT8_T'},
	CascadeManagerParameterId.PARAM_I_FACTOR:                              {'type': 'UINT8_T'},
	CascadeManagerParameterId.PARAM_D_FACTOR:                              {'type': 'UINT8_T'},
	CascadeManagerParameterId.SCHEDULE:                                    {'type': 'SCHEDULE', 'array_size': SCHEDULE_ARRAY_SIZE},
	CascadeManagerParameterId.REQUIRED_POWER:                              {'type': 'UINT8_T'},
	CascadeManagerParameterId.NEXT_TEMPERATURE_SRC_ON_DELAY:               {'type': 'UINT8_T'},
	CascadeManagerParameterId.ROTATION_TYPE:                               {'type': 'UINT8_T'},
	CascadeManagerParameterId.TEMPERATURE_OFFSET:                          {'type': 'TEMPERATURE'},
	CascadeManagerParameterId.MINIMUM_REQUIRED_TEMPERATURE:                {'type': 'TEMPERATURE'},
	CascadeManagerParameterId.MAXIMUM_REQUIRED_TEMPERATURE:                {'type': 'TEMPERATURE'},
	CascadeManagerParameterId.WORK_FUNCTION:                               {'type': 'UINT8_T'},
	CascadeManagerParameterId.TEMPERATURE_SOURCE_OFF_DELAY_BY_TEMPERATURE: {'type': 'UINT8_T'},
}

"""Metadata for DHW parameters, excluding channel pseudo-parameters."""

from smartnet.constants import DhwParameterId
from .common import SCHEDULE_ARRAY_SIZE

PARAMETER_INFO = {
	DhwParameterId.TEMPERATURE_COMFORT:           {'type': 'TEMPERATURE'},
	DhwParameterId.TEMPERATURE_DESIRED:           {'type': 'TEMPERATURE'},
	DhwParameterId.SINGLE_DHW_MODE:               {'type': 'UINT8_T'},
	DhwParameterId.DHW_RELIEF:                    {'type': 'UINT8_T'},
	DhwParameterId.CIRCULATION_MODE:              {'type': 'UINT8_T'},
	DhwParameterId.CIRCULATION_PERIOD_ON:         {'type': 'TIME_MS'},
	DhwParameterId.CIRCULATION_PERIOD_OFF:        {'type': 'TIME_MS'},
	DhwParameterId.TEMPERATURE_HYSTERESIS:        {'type': 'TEMPERATURE'},
	DhwParameterId.ANTILEGION:                    {'type': 'UINT8_T'},
	DhwParameterId.WORK_MODE:                     {'type': 'UINT8_T'},
	DhwParameterId.SCHEDULE:                      {'type': 'SCHEDULE', 'array_size': SCHEDULE_ARRAY_SIZE},
	DhwParameterId.MINIMUM_FLOW:                  {'type': 'UINT8_T'},
	DhwParameterId.SUPPLY_PUMP_KPROPORTIONAL:     {'type': 'TEMPERATURE'},
	DhwParameterId.SUPPLY_PUMP_KINTEGRATION:      {'type': 'UINT8_T'},
	DhwParameterId.FLOW_SENSOR_TYPE:              {'type': 'UINT8_T'},
	DhwParameterId.SUPPLY_PUMP_KDIFFERENTIATION:  {'type': 'UINT8_T'},
	DhwParameterId.CIRCULATION_PUMP_DELTA_T:      {'type': 'TEMPERATURE'},
	DhwParameterId.SUPPLY_PUMP_OFF_DELAY:         {'type': 'TIME_MS'},
	DhwParameterId.CURRENT_WORK_MODE_STATUS:      {'type': 'UINT8_T'},
	DhwParameterId.TEMPERATURE_ECONOM:            {'type': 'TEMPERATURE'},
	DhwParameterId.LOCATION:                      {'type': 'UINT8_T'},
}

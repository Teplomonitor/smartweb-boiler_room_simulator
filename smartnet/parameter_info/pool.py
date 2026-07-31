"""Metadata for POOL parameters."""

from smartnet.constants import SwimmingPoolParameterId
from .common import SCHEDULE_ARRAY_SIZE

PARAMETER_INFO = {
	SwimmingPoolParameterId.REQUIRED_POOL_TEMPERATURE:         {'type': 'TEMPERATURE'},
	SwimmingPoolParameterId.CURRENT_REQUIRED_POOL_TEMPERATURE: {'type': 'TEMPERATURE'},
	SwimmingPoolParameterId.WORK_MODE:                         {'type': 'UINT8_T'},
	SwimmingPoolParameterId.SCHEDULE:                          {'type': 'SCHEDULE', 'array_size': SCHEDULE_ARRAY_SIZE},
	SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_MODE:        {'type': 'UINT8_T'},
	SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_PERIOD_ON:   {'type': 'TIME_MS'},
	SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_PERIOD_OFF:  {'type': 'TIME_MS'},
	SwimmingPoolParameterId.REQUIRED_POOL_TEMPERATURE_ECONOM:  {'type': 'TEMPERATURE'},
	SwimmingPoolParameterId.FILLING_DURATION:                  {'type': 'TIME_MS'},
	SwimmingPoolParameterId.LOW_WATER_LEVEL_ALARM_RESET:       {'type': 'UINT8_T'},
	SwimmingPoolParameterId.CURRENT_WORK_MODE_STATUS:          {'type': 'UINT8_T'},
}

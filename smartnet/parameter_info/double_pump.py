"""Metadata for DOUBLE_PUMP parameters used by controller checks."""

from smartnet.constants import DoublePumpParameterId


PARAMETER_INFO = {
	DoublePumpParameterId.PUMP_1_STATUS: {'type': 'UINT8_T'},
	DoublePumpParameterId.PUMP_2_STATUS: {'type': 'UINT8_T'},
	DoublePumpParameterId.DOUBLE_POWER: {'type': 'UINT8_T'},
	DoublePumpParameterId.ALARM_STATUS: {'type': 'UINT8_T'},
}
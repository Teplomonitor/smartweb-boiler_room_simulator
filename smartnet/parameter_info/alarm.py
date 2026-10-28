"""Metadata for the indexed ALARM program parameters."""

from smartnet.constants import AlarmParameterId


PARAMETER_INFO = {
	AlarmParameterId.INPUT_TYPE: {'type': 'UINT8_T', 'array_size': 8},
	AlarmParameterId.INPUT_CONTROL: {'type': 'UINT8_T', 'array_size': 8},
	AlarmParameterId.ALARM_DELAY: {'type': 'TIME_MS', 'array_size': 8},
	AlarmParameterId.AUTO_RESET: {'type': 'UINT8_T', 'array_size': 8},
	AlarmParameterId.ENABLE_LOG: {'type': 'UINT8_T', 'array_size': 8},
}
"""Metadata for FILLING_LOOP parameters."""

from smartnet.constants import FillingLoopParameterId


PARAMETER_INFO = {
	FillingLoopParameterId.SINGLE_FILL:              {'type': 'UINT8_T'},
	FillingLoopParameterId.AUTO_FILL:                {'type': 'UINT8_T'},
	FillingLoopParameterId.PRESSURE_INPUT_TYPE:      {'type': 'UINT8_T'},
	FillingLoopParameterId.MINIMUM_PRESSURE:         {'type': 'TEMPERATURE'},
	FillingLoopParameterId.PRESSURE_HYST:            {'type': 'TEMPERATURE'},
	FillingLoopParameterId.FILLING_DURATION:         {'type': 'TIME_MS'},
	FillingLoopParameterId.PRESSURE_LOSS_ALARM_RESET: {'type': 'UINT8_T'},
	FillingLoopParameterId.AUTO_FILL_COUNTER:        {'type': 'UINT8_T'},
}

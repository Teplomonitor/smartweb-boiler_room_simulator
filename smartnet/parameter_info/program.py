"""Metadata for the generic PROGRAM parameter group."""

from smartnet.constants import ProgramParameterId

PARAMETER_INFO = {
	ProgramParameterId.ID:                  {'type': 'UINT8_T'},
	ProgramParameterId.INPUT:               {'type': 'TEMPERATURE', 'array_size': 10},
	ProgramParameterId.OUTPUT:              {'type': 'UINT8_T', 'array_size': 10},
	ProgramParameterId.TITLE:               {'type': 'STRING'},
	ProgramParameterId.INPUT_MAPPING:       {'type': 0},
	ProgramParameterId.OUTPUT_MAPPING:      {'type': 0},
	ProgramParameterId.SCHEME:              {'type': 'UINT8_T'},
	ProgramParameterId.TRAINING_ENABLED:    {'type': 'UINT8_T'},
	ProgramParameterId.MANUAL_MODE_ENABLED: {'type': 'UINT8_T'},
	ProgramParameterId.OUTPUT_MANUAL_STATE: {'type': 0},
}

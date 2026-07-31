"""Metadata for BOILER parameters, excluding channel pseudo-parameters."""

from smartnet.constants import BoilerParameterId

PARAMETER_INFO = {
	BoilerParameterId.WARMUP_TEMPERATURE:         {'type': 'TEMPERATURE'},
	BoilerParameterId.BOILER_COOLING:             {'type': 'UINT8_T'},
	BoilerParameterId.BOILER_COOLING_TEMPERATURE: {'type': 'TEMPERATURE'},
	BoilerParameterId.BACKWARD_PROTECT_T20:       {'type': 'TEMPERATURE'},
	BoilerParameterId.BACKWARD_PROTECT_T90:       {'type': 'TEMPERATURE'},
}

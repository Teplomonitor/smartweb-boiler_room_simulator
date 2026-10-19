"""Metadata for BOILER parameters, excluding channel pseudo-parameters."""

from smartnet.constants import BoilerParameterId, TemperatureGeneratorParameterId

PARAMETER_INFO = {
	BoilerParameterId.WARMUP_TEMPERATURE:         {'type': 'TEMPERATURE'},
	BoilerParameterId.BOILER_COOLING:             {'type': 'UINT8_T'},
	BoilerParameterId.BOILER_COOLING_TEMPERATURE: {'type': 'TEMPERATURE'},
	BoilerParameterId.BACKWARD_PROTECT_T20:       {'type': 'TEMPERATURE'},
	BoilerParameterId.BACKWARD_PROTECT_T90:       {'type': 'TEMPERATURE'},

	# Convenience alias for the boiler pump off delay. The actual parameter lives
	# in the temperature-generator program type, but the boiler exposes it here.
	TemperatureGeneratorParameterId.PUMP_OFF_DELAY: {'type': 'TIME_MS'},
}
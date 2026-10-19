"""Metadata for BOILER parameters, excluding channel pseudo-parameters."""

from smartnet.constants import TemperatureGeneratorParameterId

PARAMETER_INFO = {
	# Convenience alias for the boiler pump off delay. The actual parameter lives
	# in the temperature-generator program type, but the boiler exposes it here.
	TemperatureGeneratorParameterId.PUMP_OFF_DELAY: {'type': 'TIME_MS'},
}
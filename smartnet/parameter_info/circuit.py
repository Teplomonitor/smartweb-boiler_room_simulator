"""Metadata for CIRCUIT parameters."""

from smartnet.constants import CircuitParameterId

PARAMETER_INFO = {
	CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE:                 {'type': 'TEMPERATURE'},
	CircuitParameterId.HEAT_CALCULATION_MODE:                              {'type': 'UINT8_T'},
	CircuitParameterId.HEATING_SLOPE:                                      {'type': 'TDP_FLOAT'},
	CircuitParameterId.ROOM_SENSOR_INFLUENCE:                              {'type': 'UINT8_T'},
	CircuitParameterId.OUTDOOR_TEMPERATURE:                                {'type': 'TEMPERATURE'},
	CircuitParameterId.ANALOG_PUMP_CONTORL_MODE:                           {'type': 'UINT8_T'},
	CircuitParameterId.ANALOG_PUMP_MINIMUM_SPEED:                          {'type': 'UINT8_T'},
	CircuitParameterId.ANALOG_PUMP_CONSTANT_SPEED:                         {'type': 'UINT8_T'},
	CircuitParameterId.ROOM_SENSOR_INFLUENCE_MIN:                          {'type': 'TEMPERATURE'},
	CircuitParameterId.ROOM_SENSOR_INFLUENCE_MAX:                          {'type': 'TEMPERATURE'},
	CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_TEMPERATURE:          {'type': 'TEMPERATURE'},
	CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_REQUIRED_TEMPERATURE: {'type': 'TEMPERATURE'},
	CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_ID:                   {'type': 'UINT8_T'},
	CircuitParameterId.OUTSIDE_TEMPERATURE_REQUEST_VALUE:                  {'type': 'TEMPERATURE'},
	CircuitParameterId.MINIMUM_FLOW_TEMPERATURE:                           {'type': 'TEMPERATURE'},
	CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE:                           {'type': 'TEMPERATURE'},
	CircuitParameterId.ANALOG_PUMP_MAXIMUM_SPEED:                          {'type': 'UINT8_T'},
	CircuitParameterId.FLOW_CIRCULATION_IS_ACTIVE:                         {'type': 'UINT8_T'},
}

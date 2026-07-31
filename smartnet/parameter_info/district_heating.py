"""Metadata for DISTRICT_HEATING parameters."""

from smartnet.constants import DistrictHeatingParameterId

PARAMETER_INFO = {
	DistrictHeatingParameterId.PARAM_VALVE_MIN:                              {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_VALVE_RUNNING_TIME:                     {'type': 'TIME_MS'},
	DistrictHeatingParameterId.PARAM_P_FACTOR:                               {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_I_FACTOR:                               {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_D_FACTOR:                               {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_BACKWARD_CONTROL_TYPE:                  {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_SUPPLY_PUMP_CONTROL_TYPE:               {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_MAXIMUM_BACKWARD_TEMPERATURE:           {'type': 'TEMPERATURE'},
	DistrictHeatingParameterId.PARAM_MAXIMUM_BACKWARD_TEMPERATURE_II:        {'type': 'TEMPERATURE'},
	DistrictHeatingParameterId.PARAM_OUTDOOR_TEMPERATURE_II:                 {'type': 'TEMPERATURE'},
	DistrictHeatingParameterId.PARAM_THERMAL_OUTPUT_CALIBRATION:             {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_VOLUME_FLOW_CALIBRATION:                {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_MAXIMUM_THERMAL_OUTPUT:                 {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_MAXIMUM_VOLUME_FLOW:                    {'type': 'TEMPERATURE'},
	DistrictHeatingParameterId.PARAM_TEMPERATURE_SOURCE_POWER_REQUEST_DELAY: {'type': 'TIME_MS'},
	DistrictHeatingParameterId.PARAM_TEMPERATURE_SOURCE_ID:                  {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_CURRENT_MAXIMUM_BACKWARD_TEMPERATURE:   {'type': 'TEMPERATURE'},
}

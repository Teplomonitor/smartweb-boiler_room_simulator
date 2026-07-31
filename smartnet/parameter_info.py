"""
Parameter metadata definitions. Single source of truth for parameter types and properties.
Uses IntEnum keys from smartnet.constants for type safety.
"""

from smartnet.constants import (
	ProgramParameterId,
	RoomDeviceParameterId,
	ControllerParameterId,
	HeatingCircuitParameterId,
	CircuitParameterId,
	ConsumerParameterId,
	SnowMelterParameterId,
	CascadeManagerParameterId,
	DistrictHeatingParameterId,
	SwimmingPoolParameterId,
	VirtualControllerParameterId,
	ProgramType,
)

SCHEDULE_ARRAY_SIZE = 7 * 3 * 2

# Program parameters
PROGRAM_PARAMETER_INFO = {
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

# Room device parameters
ROOM_DEVICE_PARAMETER_INFO = {
	RoomDeviceParameterId.ROOM_COMFORT_TEMPERATURE:           {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.ROOM_REDUCED_TEMPERATURE:           {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.ROOM_HYSTERESIS:                    {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.RELAY_PERIOD:                       {'type': 'TIME_MS'},
	RoomDeviceParameterId.RESPONSIBLE_CIRCUIT_1:              {'type': 'UINT8_T'},
	RoomDeviceParameterId.RESPONSIBLE_CIRCUIT_2:              {'type': 'UINT8_T'},
	RoomDeviceParameterId.RESPONSIBLE_CIRCUIT_3:              {'type': 'UINT8_T'},
	RoomDeviceParameterId.WORK_MODE:                          {'type': 'UINT8_T'},
	RoomDeviceParameterId.ROOM_DEVICE_VALVE_STATE:            {'type': 'UINT8_T'},
	RoomDeviceParameterId.MINIMUM_FLOOR_TEMPERATURE:          {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.MAXIMUM_FLOOR_TEMPERATURE:          {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.RADIATOR_MINIMUM_SIGNAL:            {'type': 'UINT8_T'},
	RoomDeviceParameterId.ROOM_DESIRED_TEMPERATURE:           {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.RELAY_PERCENTAGE_PRIMARY:           {'type': 'UINT8_T'},
	RoomDeviceParameterId.RELAY_PERCENTAGE_SECONDARY:         {'type': 'UINT8_T'},
	RoomDeviceParameterId.OUTDOOR_TEMPERATURE:                {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.RELAY_PERCENTAGE_ADDITIONAL:        {'type': 'UINT8_T'},
	RoomDeviceParameterId.CIRCUIT_1_SHIFT:                    {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.CIRCUIT_2_SHIFT:                    {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.CIRCUIT_3_SHIFT:                    {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.ROOM_OFF_TEMPERATURE:               {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.SCHEDULE:                           {'type': 'SCHEDULE', 'array_size': SCHEDULE_ARRAY_SIZE},
	RoomDeviceParameterId.FLOOR_REQUIRED_TEMPERATURE:         {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.CURRENT_FLOOR_REQUIRED_TEMPERATURE: {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.WALL_REQUIRED_TEMPERATURE:          {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.CURRENT_WALL_REQUIRED_TEMPERATURE:  {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.HEAT_EXTRICATION:                   {'type': 'UINT8_T'},
	RoomDeviceParameterId.FLOOR_REDUCED_TEMPERATURE:          {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.WALL_REDUCED_TEMPERATURE:           {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.CURRENT_WORK_MODE_STATUS:           {'type': 'UINT8_T'},
	RoomDeviceParameterId.VENTILATION_CIRCUIT:                {'type': 'UINT8_T'},
	RoomDeviceParameterId.REQUIRED_HUMIDITY:                  {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.POOL_CIRCUIT:                       {'type': 'UINT8_T'},
	RoomDeviceParameterId.POOL_TEMPERATURE_OFFSET:            {'type': 'TEMPERATURE'},
	RoomDeviceParameterId.SCHEDULE_2_0:                       {'type': 'UINT8_T'},
	RoomDeviceParameterId.LOCATION:                           {'type': 'UINT8_T'},
}

# Controller parameters
CONTROLLER_PARAMETER_INFO = {
	ControllerParameterId.SENSOR:                       {'type': 0},
	ControllerParameterId.OUTPUT:                       {'type': 0},
	ControllerParameterId.USED_SENSORS_MASK:            {'type': 0},
	ControllerParameterId.USED_RELAYS_MASK:             {'type': 0},
	ControllerParameterId.TITLE:                        {'type': 0},
	ControllerParameterId.CONTROLLER_TYPE:              {'type': 0},
	ControllerParameterId.REVISION:                     {'type': 0},
	ControllerParameterId.INPUTS_MASK:                  {'type': 0},
	ControllerParameterId.OUTPUTS_MASK:                 {'type': 0},
	ControllerParameterId.ANALOG_INPUT_SIGNAL_TYPE:     {'type': 0},
	ControllerParameterId.ANALOG_INPUT_SENSOR_TYPE:     {'type': 0},
	ControllerParameterId.ANALOG_INPUT_POINT_X1:        {'type': 0},
	ControllerParameterId.ANALOG_INPUT_POINT_Y1:        {'type': 0},
	ControllerParameterId.ANALOG_INPUT_POINT_X2:        {'type': 0},
	ControllerParameterId.ANALOG_INPUT_POINT_Y2:        {'type': 0},
	ControllerParameterId.ANALOG_OUTPUT_PROFIL:         {'type': 0},
	ControllerParameterId.ANALOG_OUTPUT_SIGNAL_FORM:    {'type': 0},
	ControllerParameterId.ANALOG_OUTPUT_SIGNAL_AUS:     {'type': 0},
	ControllerParameterId.ANALOG_OUTPUT_SIGNAL_EIN:     {'type': 0},
	ControllerParameterId.ANALOG_OUTPUT_SIGNAL_MAX:     {'type': 0},
	ControllerParameterId.ANALOG_OUTPUT_DREHZAH_BEI_EIN: {'type': 0},
	ControllerParameterId.ANALOG_OUTPUT_TYP:            {'type': 0},
	ControllerParameterId.NETWORK_INPUT_CONFIG:         {'type': 0},
	ControllerParameterId.NETWORK_VAR_INPUT_CONFIG:     {'type': 0},
	ControllerParameterId.NETWORK_OUTPUT_CONFIG:        {'type': 0},
	ControllerParameterId.VARIABLE_TYPE:                {'type': 0},
	ControllerParameterId.OUTPUT_TO_VARIABLE_MAPPING:   {'type': 0},
	ControllerParameterId.DATE:                         {'type': 0},
	ControllerParameterId.TIME:                         {'type': 0},
	ControllerParameterId.SENSOR_CALIBRATION:           {'type': 0},
	ControllerParameterId.DISCRETTE_OUTPUT_SIGNAL_FORM: {'type': 0},
	ControllerParameterId.ANALOG_OUTPUT_MAX_Y:          {'type': 0},
	ControllerParameterId.SENSOR_TYPE:                  {'type': 0},
	ControllerParameterId.SENSOR_INFO:                  {'type': 0},
	ControllerParameterId.SUMMER_TIME_SWITCH:           {'type': 0},
	ControllerParameterId.TIME_MASTER:                  {'type': 0},
	ControllerParameterId.ADAPTER_TYPE:                 {'type': 0},
	ControllerParameterId.ADAPTER_SPEED:                {'type': 0},
	ControllerParameterId.ADAPTER_PARITY:               {'type': 0},
	ControllerParameterId.CONTROLLER_ID:                {'type': 0},
	ControllerParameterId.ADAPTER_STOP_BIT_NUM:         {'type': 0},
	ControllerParameterId.RELAY_TEST_ENABLE:            {'type': 0},
	ControllerParameterId.OUTPUT_MANUAL_VALUE:          {'type': 0},
}

# Heating circuit parameters
HEATING_CIRCUIT_PARAMETER_INFO = {
	HeatingCircuitParameterId.FROST_PROTECTION_TEMPERATURE:  {'type': 'TEMPERATURE'},
	HeatingCircuitParameterId.VALVE_RUNING_TIME:              {'type': 'TIME_MS'},
	HeatingCircuitParameterId.VALVE_OPEN_PROPORTIONAL_BAND:   {'type': 'TEMPERATURE'},
	HeatingCircuitParameterId.VALVE_CLOSE_PROPORTIONAL_BAND:  {'type': 'TEMPERATURE'},
	HeatingCircuitParameterId.VALVE_BLOCK:                    {'type': 'UINT8_T'},
	HeatingCircuitParameterId.PUMP_MODE:                      {'type': 'UINT8_T'},
	HeatingCircuitParameterId.PUMP_OFF_OUTDOOR_TEMPERATURE:   {'type': 'TEMPERATURE'},
	HeatingCircuitParameterId.ANALOG_CICRULATION_PUMP_STATE:  {'type': 'UINT8_T'},
	HeatingCircuitParameterId.ANALOG_HEATCHANGE_PUMP_STATE:   {'type': 'UINT8_T'},
	HeatingCircuitParameterId.VALVE_POSITION:                 {'type': 'UINT8_T'},
}

# Circuit parameters
CIRCUIT_PARAMETER_INFO = {
	CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE:                  {'type': 'TEMPERATURE'},
	CircuitParameterId.HEAT_CALCULATION_MODE:                               {'type': 'UINT8_T'},
	CircuitParameterId.HEATING_SLOPE:                                       {'type': 'TDP_FLOAT'},
	CircuitParameterId.ROOM_SENSOR_INFLUENCE:                               {'type': 'UINT8_T'},
	CircuitParameterId.OUTDOOR_TEMPERATURE:                                 {'type': 'TEMPERATURE'},
	CircuitParameterId.ANALOG_PUMP_CONTORL_MODE:                            {'type': 'UINT8_T'},
	CircuitParameterId.ANALOG_PUMP_MINIMUM_SPEED:                           {'type': 'UINT8_T'},
	CircuitParameterId.ANALOG_PUMP_CONSTANT_SPEED:                          {'type': 'UINT8_T'},
	CircuitParameterId.ROOM_SENSOR_INFLUENCE_MIN:                           {'type': 'TEMPERATURE'},
	CircuitParameterId.ROOM_SENSOR_INFLUENCE_MAX:                           {'type': 'TEMPERATURE'},
	CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_TEMPERATURE:           {'type': 'TEMPERATURE'},
	CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_REQUIRED_TEMPERATURE:  {'type': 'TEMPERATURE'},
	CircuitParameterId.CURRENT_SUPPORTED_ROOM_DEVICE_ID:                    {'type': 'UINT8_T'},
	CircuitParameterId.OUTSIDE_TEMPERATURE_REQUEST_VALUE:                   {'type': 'TEMPERATURE'},
	CircuitParameterId.MINIMUM_FLOW_TEMPERATURE:                            {'type': 'TEMPERATURE'},
	CircuitParameterId.MAXIMUM_FLOW_TEMPERATURE:                            {'type': 'TEMPERATURE'},
	CircuitParameterId.ANALOG_PUMP_MAXIMUM_SPEED:                           {'type': 'UINT8_T'},
	CircuitParameterId.FLOW_CIRCULATION_IS_ACTIVE:                          {'type': 'UINT8_T'},
}

# Consumer parameters
CONSUMER_PARAMETER_INFO = {
	ConsumerParameterId.PRIORITY:                  {'type': 'UINT8_T'},
	ConsumerParameterId.GENERATOR_ID:              {'type': 'UINT8_T'},
	ConsumerParameterId.DUMMY1:                    {'type': 'UINT8_T'},
	ConsumerParameterId.DUMMY2:                    {'type': 'UINT8_T'},
	ConsumerParameterId.TEMPERATURE_COMPENSATION:  {'type': 'TEMPERATURE'},
	ConsumerParameterId.REQUIRED_TEMPERATURE:      {'type': 'TEMPERATURE'},
	ConsumerParameterId.GENERATOR_TEMPERATURE:     {'type': 'TEMPERATURE'},
	ConsumerParameterId.HEAT_EXTRICATION_ENABLED:  {'type': 'UINT8_T'},
	ConsumerParameterId.ALARM_PROGRAM_ID:          {'type': 'UINT8_T'},
}

# Snow melter parameters
SNOWMELTER_PARAMETER_INFO = {
	SnowMelterParameterId.WORK_MODE:                                               {'type': 'UINT8_T'},
	SnowMelterParameterId.MINIMUM_OUTDOOR_TEMPERATURE:                             {'type': 'TEMPERATURE'},
	SnowMelterParameterId.MAXIMUM_OUTDOOR_TEMPERATURE:                             {'type': 'TEMPERATURE'},
	SnowMelterParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE_OF_SECONDARY_CIRCUIT: {'type': 'TEMPERATURE'},
	SnowMelterParameterId.OUTDOOR_TEMPERATURE:                                     {'type': 'TEMPERATURE'},
	SnowMelterParameterId.PRIMARY_CIRCUIT_PROTECTION_TEMPERATURE:                  {'type': 'TEMPERATURE'},
	SnowMelterParameterId.REQUIRED_PLATE_TEMPERATURE:                              {'type': 'TEMPERATURE'},
}

# Cascade manager parameters
CASCADE_SOURCES_MAX_NUM = 8

CASCADE_MANAGER_PARAMETER_INFO = {
	CascadeManagerParameterId.PARAM_ROTATION_PERIOD:                         {'type': 'UINT8_T'},
	CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID:                   {'type': 'UINT8_T', 'array_size': CASCADE_SOURCES_MAX_NUM},
	CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_TYPE:                 {'type': 'UINT8_T', 'array_size': CASCADE_SOURCES_MAX_NUM},
	CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_POWER:                {'type': 'UINT8_T', 'array_size': CASCADE_SOURCES_MAX_NUM},
	CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_WORKTIME:             {'type': 'UINT8_T', 'array_size': CASCADE_SOURCES_MAX_NUM},
	CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_PRIORITY:             {'type': 'UINT8_T', 'array_size': CASCADE_SOURCES_MAX_NUM},
	CascadeManagerParameterId.PARAM_P_FACTOR:                                {'type': 'UINT8_T'},
	CascadeManagerParameterId.PARAM_I_FACTOR:                                {'type': 'UINT8_T'},
	CascadeManagerParameterId.PARAM_D_FACTOR:                                {'type': 'UINT8_T'},
	CascadeManagerParameterId.SCHEDULE:                                      {'type': 'SCHEDULE', 'array_size': SCHEDULE_ARRAY_SIZE},
	CascadeManagerParameterId.REQUIRED_POWER:                                {'type': 'UINT8_T'},
	CascadeManagerParameterId.NEXT_TEMPERATURE_SRC_ON_DELAY:                 {'type': 'UINT8_T'},
	CascadeManagerParameterId.ROTATION_TYPE:                                 {'type': 'UINT8_T'},
	CascadeManagerParameterId.TEMPERATURE_OFFSET:                            {'type': 'TEMPERATURE'},
	CascadeManagerParameterId.MINIMUM_REQUIRED_TEMPERATURE:                  {'type': 'TEMPERATURE'},
	CascadeManagerParameterId.MAXIMUM_REQUIRED_TEMPERATURE:                  {'type': 'TEMPERATURE'},
	CascadeManagerParameterId.WORK_FUNCTION:                                 {'type': 'UINT8_T'},
	CascadeManagerParameterId.TEMPERATURE_SOURCE_OFF_DELAY_BY_TEMPERATURE:   {'type': 'UINT8_T'},
}

# District heating parameters
DISTRICT_HEATING_PARAMETER_INFO = {
	DistrictHeatingParameterId.PARAM_VALVE_MIN:                               {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_VALVE_RUNNING_TIME:                      {'type': 'TIME_MS'},
	DistrictHeatingParameterId.PARAM_P_FACTOR:                                {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_I_FACTOR:                                {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_D_FACTOR:                                {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_BACKWARD_CONTROL_TYPE:                   {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_SUPPLY_PUMP_CONTROL_TYPE:                {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_MAXIMUM_BACKWARD_TEMPERATURE:            {'type': 'TEMPERATURE'},
	DistrictHeatingParameterId.PARAM_MAXIMUM_BACKWARD_TEMPERATURE_II:         {'type': 'TEMPERATURE'},
	DistrictHeatingParameterId.PARAM_OUTDOOR_TEMPERATURE_II:                  {'type': 'TEMPERATURE'},
	DistrictHeatingParameterId.PARAM_THERMAL_OUTPUT_CALIBRATION:              {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_VOLUME_FLOW_CALIBRATION:                 {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_MAXIMUM_THERMAL_OUTPUT:                  {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_MAXIMUM_VOLUME_FLOW:                     {'type': 'TEMPERATURE'},
	DistrictHeatingParameterId.PARAM_TEMPERATURE_SOURCE_POWER_REQUEST_DELAY:  {'type': 'TIME_MS'},
	DistrictHeatingParameterId.PARAM_TEMPERATURE_SOURCE_ID:                   {'type': 'UINT8_T'},
	DistrictHeatingParameterId.PARAM_CURRENT_MAXIMUM_BACKWARD_TEMPERATURE:    {'type': 'TEMPERATURE'},
}

# Swimming pool parameters
SWIMMING_POOL_PARAMETER_INFO = {
	SwimmingPoolParameterId.REQUIRED_POOL_TEMPERATURE:          {'type': 'TEMPERATURE'},
	SwimmingPoolParameterId.CURRENT_REQUIRED_POOL_TEMPERATURE:  {'type': 'TEMPERATURE'},
	SwimmingPoolParameterId.WORK_MODE:                          {'type': 'UINT8_T'},
	SwimmingPoolParameterId.SCHEDULE:                           {'type': 'SCHEDULE', 'array_size': SCHEDULE_ARRAY_SIZE},
	SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_MODE:         {'type': 'UINT8_T'},
	SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_PERIOD_ON:    {'type': 'TIME_MS'},
	SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_PERIOD_OFF:   {'type': 'TIME_MS'},
	SwimmingPoolParameterId.REQUIRED_POOL_TEMPERATURE_ECONOM:   {'type': 'TEMPERATURE'},
	SwimmingPoolParameterId.FILLING_DURATION:                   {'type': 'TIME_MS'},
	SwimmingPoolParameterId.LOW_WATER_LEVEL_ALARM_RESET:        {'type': 'UINT8_T'},
	SwimmingPoolParameterId.CURRENT_WORK_MODE_STATUS:           {'type': 'UINT8_T'},
}

# Virtual controller parameters
VIRTUAL_CONTROLLER_PARAMETER_INFO = {
	VirtualControllerParameterId.CONTROLLERID:  {'type': 'UINT8_T'},
	VirtualControllerParameterId.SENSOR01:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR02:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR03:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR04:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR05:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR06:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR07:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR08:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR09:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR10:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR11:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR12:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR13:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR14:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR15:      {'type': 'TEMPERATURE'},
	VirtualControllerParameterId.SENSOR16:      {'type': 'TEMPERATURE'},
}

# Map ProgramType to parameter metadata (with IntEnum members as keys)
ParameterDict = {
	ProgramType.PROGRAM           : PROGRAM_PARAMETER_INFO,
	ProgramType.ROOM_DEVICE       : ROOM_DEVICE_PARAMETER_INFO,
	ProgramType.CONTROLLER        : CONTROLLER_PARAMETER_INFO,
	ProgramType.HEATING_CIRCUIT   : HEATING_CIRCUIT_PARAMETER_INFO,
	ProgramType.CONSUMER          : CONSUMER_PARAMETER_INFO,
	ProgramType.CASCADE_MANAGER   : CASCADE_MANAGER_PARAMETER_INFO,
	ProgramType.DISTRICT_HEATING  : DISTRICT_HEATING_PARAMETER_INFO,
	ProgramType.SNOWMELT          : SNOWMELTER_PARAMETER_INFO,
	ProgramType.CIRCUIT           : CIRCUIT_PARAMETER_INFO,
	ProgramType.POOL              : SWIMMING_POOL_PARAMETER_INFO,
	ProgramType.VIRTUAL_CONTROLLER: VIRTUAL_CONTROLLER_PARAMETER_INFO,
}

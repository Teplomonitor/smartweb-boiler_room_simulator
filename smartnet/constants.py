
requestFlag = {
	'REQUEST' :0x00, 
	'RESPONSE':0x10, 
}

ControllerType = {
	'UNDEFINED'     :  0,
	'STDC'          :  1,
	'LTDC'          :  2,
	'XHCC'          :  3,
	'SWN'           :  4,
	'SWD'           :  5,
	'CALEON'        :  6,
	'XHCC_S62'      :  7,
	'LTDC_S45'      :  8,
	'VIRTUAL'       :  9,
	'SWK'           : 10,
	'SWK_1'         : 11,
	'CWC_CAN'       : 12,
	'CALEON_RC50'   : 13,
	'EXT_CONTROLLER': 14,
	'CALEONBOX'     : 15,
}

ProgramType = {
	'CAN_PROGRAM_TYPE_UNDEFINED' :  0,
	'PROGRAM'                    :  1,
	'OUTDOOR_SENSOR'             :  2,
	'CONSUMER'                   :  3,
	'CASCADE_MANAGER'            :  4,
	'ROOM_DEVICE'                :  5,
	'TEMPERATURE_SOURCE'         :  6,
	'HEAT_ACCUMULATOR'           :  7,
	'EXTENDED_CONTROLLER'        :  8,
	'EXTENSION_CONTROLLER'       :  9,
	'MONITORING_DEVICE'          : 10,
	'CONTROLLER'                 : 11,
	'CIRCUIT'                    : 12,
	'SCHEDULE'                   : 13,
	'HEATING_CIRCUIT'            : 14,
	'DISTRICT_HEATING'           : 15,
	'DHW'                        : 16,
	'FLOW_THROUGH_DHW'           : 17,
	'TEMPERATURE_GENERATOR'      : 18,
	'POOL'                       : 19,
	'THERMOSTAT'                 : 20,
	'SNOWMELT'                   : 21,
	'REMOTE_CONTROL'             : 22,
	'BOILER'                     : 23,
	'CHILLER'                    : 24,
	'SOLAR_COLLECTOR'            : 25,
	'VENTILATION'                : 26,
	'GENERIC_RELAY'              : 27,
	'ALARM'                      : 28,
	'FILLING_LOOP'               : 29,
	
	'VIRTUAL_CONTROLLER'         : 30,
	'DOUBLE_PUMP'                : 31,
	'LIN_CONTROLLER'             : 32,
	'LIN_PUMP'                   : 33,
	'OPEN_THERM_BOILER'          : 34,
	'MODBUS_TEMPERATURE_SOURCE'  : 35,
	'MB_OT_ADAPTER'              : 36,
	'MODBUS_SENSOR'              : 37,
	'NAVIEN_CASCADE_MANAGER'     : 38,
	'NAVIEN_NFB'                 : 39,
	'WAREHOUSE_AREA'             : 40,
	'CWC_LORA_ADAPTER'           : 32, #//TODO: change ID to 41
	'TPT_VALVE_ADAPTER'          : 42,
	
	
	'DATALOGGER_MONITOR'       : 0x80,  
	'EVENT'                    : 0x81, 
	'FWC_CASCADE'              : 0x82,  # freshwater controller cascading functions
	'DATALOGGER_NAMEDSENSORS'  : 0x83,  # request sensor values by name eg. outdor room temperature/humidity rc switch or get changes
	'HCC'                      : 0x84,  # heating circuit control program eg. heat request
	'DL_CONFIGMENU_DATALOGGER' : 0x85,  # datalogger configuration receiver is datalogger                                                                          
	'DL_CONFIGMENU_CONTROLLER' : 0x86,  # receiver is controller                                                                                                    
	'CLOCKSYNC'                : 0x87,  # send/receive date and time                                                                                                
	'REMOTERELAY'              : 0x88,  # set relay from external controller                                                                                        
	'HOLIDAYRETURNDATE'        : 0x89,  # holiday return date                                                                                                       
	'DAYSCHEDULE'              : 0x8A,  # day schedule function type is used to select day of the week 0 = monday 7 messages needed for week schedule            
	'AVAILABLERESOURCES'       : 0x8B,  # sending available resources (relays sensors ...) on request ore at startup                                              
	'PARAMETERSYNC'            : 0x8C,  # sending parameter values from one device to an other parameter list / functionId is defined in exfuncIDs.h (teFunctionId)
	'RESOURCEDATA1WIRE'        : 0x8D,  # sending additional data of resource on request (1wire ROM data)                                                           
	'FILETRANSFER'             : 0x8E,  # send multiple can packets                                                                                                 
	'PARAMETERSYNCCONFIG'      : 0x8F,  # configuration for parameter sync factory reset ...                                                                      
	'ROOMSYNC'                 : 0x90,  # special PARAMETERSYNC for vhcData (no destination check)                                                                  
	'PANIC'                    : 0x91,  # tells other controllers to slow down CAN packet transfer frequency                                                        
	'VHCDATA_UPDATE'           : 0x92,  # function:0 broadcast last manual mode change                                                                              
	'MSGLOG'                   : 0x93,  # global message log: Function = message severity Data = [4 byte param1 2 byte param2 2 byte message code]
	'CHARLIE'                  : 0xC0,
}

ProgramParameter = {
	'ID'                 : {'id': 0, 'type': 0},
	'INPUT'              : {'id': 1, 'type': 0},
	'OUTPUT'             : {'id': 2, 'type': 0},
	'TITLE'              : {'id': 3, 'type': 0},
	'INPUT_MAPPING'      : {'id': 4, 'type': 0},
	'OUTPUT_MAPPING'     : {'id': 5, 'type': 0},
	'SCHEME'             : {'id': 6, 'type': 0},
	'TRAINING_ENABLED'   : {'id': 7, 'type': 0},
	'MANUAL_MODE_ENABLED': {'id': 8, 'type': 0},
	'OUTPUT_MANUAL_STATE': {'id': 9, 'type': 0},
}

ProgramScheme = {
	'DEFAULT' : 0,

	'CIRCUIT_MIXED'         : 0,
	'CIRCUIT_HEAT_EXCHANGE' : 1,
	'CIRCUIT_DIRECT'        : 2,
	'CIRCUIT_HEATING_LINE'  : 3,
	
	
	'PROGRAM_SCHEME_0': 0,
	'PROGRAM_SCHEME_1': 1,
	'PROGRAM_SCHEME_2': 2,
	'PROGRAM_SCHEME_3': 3,
	'PROGRAM_SCHEME_4': 4,
	'PROGRAM_SCHEME_5': 5,
}

RoomDeviceParameter = {                             
	'ROOM_COMFORT_TEMPERATURE'          : {'id':  1, 'type': 'TEMPERATURE'},
	'ROOM_REDUCED_TEMPERATURE'          : {'id':  2, 'type': 'TEMPERATURE'},
	'ROOM_HYSTERESIS'                   : {'id':  3, 'type': 'TEMPERATURE'},
	'RELAY_PERIOD'                      : {'id':  4, 'type': 'TIME_MS'},
	'RESPONSIBLE_CIRCUIT_1'             : {'id':  5, 'type': 'UINT8_T'},
	'RESPONSIBLE_CIRCUIT_2'             : {'id':  6, 'type': 'UINT8_T'},
	'RESPONSIBLE_CIRCUIT_3'             : {'id':  7, 'type': 'UINT8_T'},
	'WORK_MODE'                         : {'id':  8, 'type': 'UINT8_T'},
	'ROOM_DEVICE_VALVE_STATE'           : {'id':  9, 'type': 'UINT8_T'},
	'MINIMUM_FLOOR_TEMPERATURE'         : {'id': 10, 'type': 'TEMPERATURE'},
	'MAXIMUM_FLOOR_TEMPERATURE'         : {'id': 11, 'type': 'TEMPERATURE'},
	'RADIATOR_MINIMUM_SIGNAL'           : {'id': 12, 'type': 'UINT8_T'},
	'ROOM_DESIRED_TEMPERATURE'          : {'id': 13, 'type': 'TEMPERATURE'},
	'RELAY_PERCENTAGE_PRIMARY'          : {'id': 14, 'type': 'UINT8_T'},
	'RELAY_PERCENTAGE_SECONDARY'        : {'id': 15, 'type': 'UINT8_T'},
	'OUTDOOR_TEMPERATURE'               : {'id': 16, 'type': 'TEMPERATURE'},
	'RELAY_PERCENTAGE_ADDITIONAL'       : {'id': 17, 'type': 'UINT8_T'},
	'CIRCUIT_1_SHIFT'                   : {'id': 18, 'type': 'TEMPERATURE'},
	'CIRCUIT_2_SHIFT'                   : {'id': 19, 'type': 'TEMPERATURE'},
	'CIRCUIT_3_SHIFT'                   : {'id': 20, 'type': 'TEMPERATURE'},
	'ROOM_OFF_TEMPERATURE'              : {'id': 21, 'type': 'TEMPERATURE'},
	'SCHEDULE'                          : {'id': 22, 'type': 'SCHEDULE'},
	'FLOOR_REQUIRED_TEMPERATURE'        : {'id': 23, 'type': 'TEMPERATURE'},
	'CURRENT_FLOOR_REQUIRED_TEMPERATURE': {'id': 24, 'type': 'TEMPERATURE'},
	'WALL_REQUIRED_TEMPERATURE'         : {'id': 25, 'type': 'TEMPERATURE'},
	'CURRENT_WALL_REQUIRED_TEMPERATURE' : {'id': 26, 'type': 'TEMPERATURE'},
	'HEAT_EXTRICATION'                  : {'id': 27, 'type': 'UINT8_T'},
	'FLOOR_REDUCED_TEMPERATURE'         : {'id': 28, 'type': 'TEMPERATURE'},
	'WALL_REDUCED_TEMPERATURE'          : {'id': 29, 'type': 'TEMPERATURE'},
	'CURRENT_WORK_MODE_STATUS'          : {'id': 30, 'type': 'UINT8_T'},
	'VENTILATION_CIRCUIT'               : {'id': 31, 'type': 'UINT8_T'},
	'REQUIRED_HUMIDITY'                 : {'id': 32, 'type': 'TEMPERATURE'},
	'POOL_CIRCUIT'                      : {'id': 33, 'type': 'UINT8_T'},
	'POOL_TEMPERATURE_OFFSET'           : {'id': 34, 'type': 'TEMPERATURE'},

	'SCHEDULE_2_0': 35,
	'LOCATION'    : 36,
}

ControllerParameter = {
	'SENSOR'                       : {'id':  1, 'type': 0},
	'OUTPUT'                       : {'id':  2, 'type': 0},
	'USED_SENSORS_MASK'            : {'id':  3, 'type': 0},
	'USED_RELAYS_MASK'             : {'id':  4, 'type': 0},
	'TITLE'                        : {'id':  5, 'type': 0},
	'CONTROLLER_TYPE'              : {'id':  6, 'type': 0},
	'REVISION'                     : {'id':  7, 'type': 0},
	'INPUTS_MASK'                  : {'id':  8, 'type': 0},
	'OUTPUTS_MASK'                 : {'id':  9, 'type': 0},
	'ANALOG_INPUT_SIGNAL_TYPE'     : {'id': 10, 'type': 0},
	'ANALOG_INPUT_SENSOR_TYPE'     : {'id': 11, 'type': 0},
	'ANALOG_INPUT_POINT_X1'        : {'id': 12, 'type': 0},
	'ANALOG_INPUT_POINT_Y1'        : {'id': 13, 'type': 0},
	'ANALOG_INPUT_POINT_X2'        : {'id': 14, 'type': 0},
	'ANALOG_INPUT_POINT_Y2'        : {'id': 15, 'type': 0},
	'ANALOG_OUTPUT_PROFIL'         : {'id': 16, 'type': 0},
	'ANALOG_OUTPUT_SIGNAL_FORM'    : {'id': 17, 'type': 0},
	'ANALOG_OUTPUT_SIGNAL_AUS'     : {'id': 18, 'type': 0},
	'ANALOG_OUTPUT_SIGNAL_EIN'     : {'id': 19, 'type': 0},
	'ANALOG_OUTPUT_SIGNAL_MAX'     : {'id': 20, 'type': 0},
	'ANALOG_OUTPUT_DREHZAH_BEI_EIN': {'id': 21, 'type': 0},
	'ANALOG_OUTPUT_TYP'            : {'id': 22, 'type': 0},
	'NETWORK_INPUT_CONFIG'         : {'id': 23, 'type': 0},
	'NETWORK_VAR_INPUT_CONFIG'     : {'id': 24, 'type': 0},
	'NETWORK_OUTPUT_CONFIG'        : {'id': 25, 'type': 0},
	'VARIABLE_TYPE'                : {'id': 26, 'type': 0},
	'OUTPUT_TO_VARIABLE_MAPPING'   : {'id': 27, 'type': 0},
	'DATE'                         : {'id': 28, 'type': 0},
	'TIME'                         : {'id': 29, 'type': 0},
	'SENSOR_CALIBRATION'           : {'id': 30, 'type': 0},
	'DISCRETTE_OUTPUT_SIGNAL_FORM' : {'id': 31, 'type': 0},
	'ANALOG_OUTPUT_MAX_Y'          : {'id': 32, 'type': 0},
	
	'SENSOR_TYPE'                  : {'id': 33, 'type': 0},
	'SENSOR_INFO'                  : {'id': 34, 'type': 0},

	'SUMMER_TIME_SWITCH'           : {'id': 35, 'type': 0}, 
	'TIME_MASTER'                  : {'id': 36, 'type': 0},
	'ADAPTER_TYPE'                 : {'id': 37, 'type': 0}, 
	'ADAPTER_SPEED'                : {'id': 38, 'type': 0}, 
	'ADAPTER_PARITY'               : {'id': 39, 'type': 0}, 

	'CONTROLLER_ID'                : {'id': 40, 'type': 0}, 

	'ADAPTER_STOP_BIT_NUM'         : {'id': 41, 'type': 0}, 

	'RELAY_TEST_ENABLE'            : {'id': 42, 'type': 0}, 

	'OUTPUT_MANUAL_VALUE'          : {'id': 43, 'type': 0}, 
}


HeatingCircuitParameter = {
	'FROST_PROTECTION_TEMPERATURE'  : {'id':  1, 'type': 'TEMPERATURE'},
	'VALVE_RUNING_TIME'             : {'id':  2, 'type': 'TIME_MS'},
	'VALVE_OPEN_PROPORTIONAL_BAND'  : {'id':  3, 'type': 'TEMPERATURE'},
	'VALVE_CLOSE_PROPORTIONAL_BAND' : {'id':  4, 'type': 'TEMPERATURE'},
	'VALVE_BLOCK'                   : {'id':  5, 'type': 'UINT8_T'},
	'PUMP_MODE'                     : {'id':  6, 'type': 'UINT8_T'},
	'PUMP_OFF_OUTDOOR_TEMPERATURE'  : {'id':  7, 'type': 'TEMPERATURE'},
	'ANALOG_CICRULATION_PUMP_STATE' : {'id':  8, 'type': 'UINT8_T'},
	'ANALOG_HEATCHANGE_PUMP_STATE'  : {'id':  9, 'type': 'UINT8_T'},
	'VALVE_POSITION'                : {'id': 10, 'type': 'UINT8_T'},
}                       

CircuitParameter = {
		'REQUIRED_CONSTANT_FLOW_TEMPERATURE'                 : {'id':  1, 'type': 'TEMPERATURE'},
		'HEAT_CALCULATION_MODE'                              : {'id':  2, 'type': 'UINT8_T'},
		'HEATING_SLOPE'                                      : {'id':  3, 'type': 'TDP_FLOAT'},
		'ROOM_SENSOR_INFLUENCE'                              : {'id':  4, 'type': 'UINT8_T'},
		'OUTDOOR_TEMPERATURE'                                : {'id':  5, 'type': 'TEMPERATURE'},
		'ANALOG_PUMP_CONTORL_MODE'                           : {'id':  6, 'type': 'UINT8_T'},
		'ANALOG_PUMP_MINIMUM_SPEED'                          : {'id':  7, 'type': 'UINT8_T'},
		'ANALOG_PUMP_CONSTANT_SPEED'                         : {'id':  8, 'type': 'UINT8_T'},
		'ROOM_SENSOR_INFLUENCE_MIN'                          : {'id':  9, 'type': 'TEMPERATURE'},
		'ROOM_SENSOR_INFLUENCE_MAX'                          : {'id': 10, 'type': 'TEMPERATURE'},
		'CURRENT_SUPPORTED_ROOM_DEVICE_TEMPERATURE'          : {'id': 11, 'type': 'TEMPERATURE'},
		'CURRENT_SUPPORTED_ROOM_DEVICE_REQUIRED_TEMPERATURE' : {'id': 12, 'type': 'TEMPERATURE'},
		'CURRENT_SUPPORTED_ROOM_DEVICE_ID'                   : {'id': 13, 'type': 'UINT8_T'},
		'OUTSIDE_TEMPERATURE_REQUEST_VALUE'                  : {'id': 14, 'type': 'TEMPERATURE'},
		'MINIMUM_FLOW_TEMPERATURE'                           : {'id': 15, 'type': 'TEMPERATURE'},
		'MAXIMUM_FLOW_TEMPERATURE'                           : {'id': 16, 'type': 'TEMPERATURE'},
		'ANALOG_PUMP_MAXIMUM_SPEED'                          : {'id': 17, 'type': 'UINT8_T'},
		'FLOW_CIRCULATION_IS_ACTIVE'                         : {'id': 18, 'type': 'UINT8_T'},
}

ConsumerParameter = {
	'PRIORITY'                  : {'id': 1, 'type': 0}, 
	'GENERATOR_ID'              : {'id': 2, 'type': 0}, 
	'DUMMY1'                    : {'id': 3, 'type': 0}, 
	'DUMMY2'                    : {'id': 4, 'type': 0}, 
	'TEMPERATURE_COMPENSATION'  : {'id': 5, 'type': 0}, 
	'REQUIRED_TEMPERATURE'      : {'id': 6, 'type': 0}, 
	'GENERATOR_TEMPERATURE'     : {'id': 7, 'type': 0}, 
	'HEAT_EXTRICATION_ENABLED'  : {'id': 8, 'type': 0}, 
	'ALARM_PROGRAM_ID'          : {'id': 9, 'type': 0}, 
}

SnowMelterParameter = {
	'WORK_MODE'                                               : {'id':  1, 'type': 0},
	'MINIMUM_OUTDOOR_TEMPERATURE'                             : {'id':  2, 'type': 0},
	'MAXIMUM_OUTDOOR_TEMPERATURE'                             : {'id':  3, 'type': 0},
	'REQUIRED_CONSTANT_FLOW_TEMPERATURE_OF_SECONDARY_CIRCUIT' : {'id':  4, 'type': 0},
	'OUTDOOR_TEMPERATURE'                                     : {'id':  5, 'type': 0},
	'PRIMARY_CIRCUIT_PROTECTION_TEMPERATURE'                  : {'id':  6, 'type': 0},
	'REQUIRED_PLATE_TEMPERATURE'                              : {'id':  7, 'type': 0},
}

CascadeManagerParameter = {
	'PARAM_ROTATION_PERIOD'                        : {'id':  1, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_ID'                  : {'id':  2, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_TYPE'                : {'id':  3, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_POWER'               : {'id':  4, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_WORKTIME'            : {'id':  5, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_PRIORITY'            : {'id':  6, 'type': 0},
	'PARAM_P_FACTOR'                               : {'id':  7, 'type': 0},
	'PARAM_I_FACTOR'                               : {'id':  8, 'type': 0},
	'PARAM_D_FACTOR'                               : {'id':  9, 'type': 0},
	'SCHEDULE'                                     : {'id': 10, 'type': 0},
	'REQUIRED_POWER'                               : {'id': 11, 'type': 0},
	'NEXT_TEMPERATURE_SRC_ON_DELAY'                : {'id': 12, 'type': 0},
	'ROTATION_TYPE'                                : {'id': 13, 'type': 0},
	'TEMPERATURE_OFFSET'                           : {'id': 14, 'type': 0},
	'MINIMUM_REQUIRED_TEMPERATURE'                 : {'id': 15, 'type': 0},
	'MAXIMUM_REQUIRED_TEMPERATURE'                 : {'id': 16, 'type': 0},
	'WORK_FUNCTION'                                : {'id': 17, 'type': 0},
	'TEMPERATURE_SOURCE_OFF_DELAY_BY_TEMPERATURE'  : {'id': 18, 'type': 0},
}

CascadeManagerParameter = {
	'PARAM_ROTATION_PERIOD'                        : {'id':  1, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_ID'                  : {'id':  2, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_TYPE'                : {'id':  3, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_POWER'               : {'id':  4, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_WORKTIME'            : {'id':  5, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_PRIORITY'            : {'id':  6, 'type': 0},
	'PARAM_P_FACTOR'                               : {'id':  7, 'type': 0},
	'PARAM_I_FACTOR'                               : {'id':  8, 'type': 0},
	'PARAM_D_FACTOR'                               : {'id':  9, 'type': 0},
	'SCHEDULE'                                     : {'id': 10, 'type': 0},
	'REQUIRED_POWER'                               : {'id': 11, 'type': 0},
	'NEXT_TEMPERATURE_SRC_ON_DELAY'                : {'id': 12, 'type': 0},
	'ROTATION_TYPE'                                : {'id': 13, 'type': 0},
	'TEMPERATURE_OFFSET'                           : {'id': 14, 'type': 0},
	'MINIMUM_REQUIRED_TEMPERATURE'                 : {'id': 15, 'type': 0},
	'MAXIMUM_REQUIRED_TEMPERATURE'                 : {'id': 16, 'type': 0},
	'WORK_FUNCTION'                                : {'id': 17, 'type': 0},
	'TEMPERATURE_SOURCE_OFF_DELAY_BY_TEMPERATURE'  : {'id': 18, 'type': 0},
}

DistrictHeatingParameter = {
	'PARAM_VALVE_MIN'                              : {'id':  1, 'type': 0},
	'PARAM_VALVE_RUNNING_TIME'                     : {'id':  2, 'type': 0},
	'PARAM_P_FACTOR'                               : {'id':  3, 'type': 0},
	'PARAM_I_FACTOR'                               : {'id':  4, 'type': 0},
	'PARAM_D_FACTOR'                               : {'id':  5, 'type': 0},
	'PARAM_BACKWARD_CONTROL_TYPE'                  : {'id':  6, 'type': 0},
	'PARAM_SUPPLY_PUMP_CONTROL_TYPE'               : {'id':  7, 'type': 0},
	'PARAM_MAXIMUM_BACKWARD_TEMPERATURE'           : {'id':  8, 'type': 0},
	'PARAM_MAXIMUM_BACKWARD_TEMPERATURE_II'        : {'id':  9, 'type': 0},
	'PARAM_OUTDOOR_TEMPERATURE_II'                 : {'id': 10, 'type': 0},
	'PARAM_THERMAL_OUTPUT_CALIBRATION'             : {'id': 11, 'type': 0},
	'PARAM_VOLUME_FLOW_CALIBRATION'                : {'id': 12, 'type': 0},
	'PARAM_MAXIMUM_THERMAL_OUTPUT'                 : {'id': 13, 'type': 0},
	'PARAM_MAXIMUM_VOLUME_FLOW'                    : {'id': 14, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_POWER_REQUEST_DELAY' : {'id': 15, 'type': 0},
	'PARAM_TEMPERATURE_SOURCE_ID'                  : {'id': 16, 'type': 0},
	'PARAM_CURRENT_MAXIMUM_BACKWARD_TEMPERATURE'   : {'id': 17, 'type': 0},
}

SwimmingPoolParameter = {
	'REQUIRED_POOL_TEMPERATURE'         : {'id':  1, 'type': 0},
	'CURRENT_REQUIRED_POOL_TEMPERATURE' : {'id':  2, 'type': 0},
	'WORK_MODE'                         : {'id':  3, 'type': 0},
	'SCHEDULE'                          : {'id':  4, 'type': 0},
	'CIRCULATION_PUMP_WORK_MODE'        : {'id':  5, 'type': 0},
	'CIRCULATION_PUMP_WORK_PERIOD_ON'   : {'id':  6, 'type': 0},
	'CIRCULATION_PUMP_WORK_PERIOD_OFF'  : {'id':  7, 'type': 0},
	'REQUIRED_POOL_TEMPERATURE_ECONOM'  : {'id':  8, 'type': 0},
	'FILLING_DURATION'                  : {'id':  9, 'type': 0},
	'LOW_WATER_LEVEL_ALARM_RESET'       : {'id': 10, 'type': 0},
	'CURRENT_WORK_MODE_STATUS'          : {'id': 11, 'type': 0},
}

ParameterDict = {
	'PROGRAM'         : ProgramParameter,
	'ROOM_DEVICE'     : RoomDeviceParameter,
	'CONTROLLER'      : ControllerParameter,
	'HEATING_CIRCUIT' : HeatingCircuitParameter,
	'CONSUMER'        : ConsumerParameter,
	'CASCADE_MANAGER' : CascadeManagerParameter,
	'DISTRICT_HEATING': DistrictHeatingParameter,
	'SNOWMELT'        : SnowMelterParameter,
	'CIRCUIT'         : CircuitParameter,
	'POOL'            : SwimmingPoolParameter,
}


ProgramFunction = {
	 'IS_ID_OCCUPIED'                 : 1,
	 'IS_TYPE_SUPPORTED'              : 2,
	 'GET_PROGRAM_TYPE'               : 3,
	 'GET_PROGRAM_NAME'               : 4,
	 'GET_PROGRAM_TYPES'              : 5,
	 'GET_SMARTNET_PROTOCOL_VERSION'  : 6,
	 'I_AM_PROGRAM'                   : 7,
	 'IS_COLLISION'                   : 8,
	 'MY_ID_CHANGED'                  : 9,
}



ControllerFunction = {
	'HAS_ANYBODY_HERE'               :  0,
	'I_AM_HERE'                      :  1,
	'GET_CONTROLLER'                 :  2,
	'GET_ACTIVE_PROGRAMS_LIST'       :  3,
	'ADD_NEW_PROGRAM'                :  4,
	'REMOVE_PROGRAM'                 :  5,
	'GET_SYSTEM_DATE_TIME'           :  6,
	'SET_SYSTEM_DATE_TIME'           :  7,
	'GET_CONTROLLER_TYPE'            :  8,
	'GET_PROGRAM_VERSION'            :  9,
	'GET_CHANNEL_NUMBER'             : 10,
	'GET_OUTPUT_TYPE'                : 11,
	'GET_INPUT_TYPE'                 : 12,
	'GET_CHANNEL_BINDING'            : 13,
	'GET_INPUT_VALUE'                : 14,
	'SET_OUTPUT_VALUE'               : 15,
	'HAS_ERROR'                      : 16,
	'GET_CONTROLLER_MASKS'           : 17,
	'GET_CHANNELS_INFO'              : 18,
	'GET_OUTPUT_VALUE'               : 19,
	'TIME_MASTER_IS_ACTIVE'          : 20,
	'JOURNAL'                        : 21,
	'GET_VARIABLE'                   : 22,
	'SET_VARIABLE'                   : 23,
	'GET_RELAY_MAPPING'              : 24,
	'SET_RELAY_MAPPING'              : 25,
	'RESET_TO_DEFAULTS'              : 26,
	'RESET_PROGRAMS'                 : 27,
	'MARK_JOURNAL_MESSAGES_AS_READ'  : 28,
	'I_AM_RESETED'                   : 40,
	'DATALOGGER_TEST'                : 41,    
	'IS_ANYBODY_HERE_CAN2'           : 42,                                    # IS_ANYBODY_HERE that comes over CAN2 or is routed CAN2 -> CAN1
	'I_AM_HERE_CAN2'                 : 43,                                    # I_AM_HERE that comes over CAN2 or is routed CAN2 -> CAN1
	'I_AM_RESETED_CAN2'              : 44,                                    # I_AM_RESETED that comes over CAN2 or is routed CAN2 -> CAN1
	'GET_FW_VERSION'                 : 60, 
	'INSTALL_FW_UPDATE'              : 61, 
	'SYSTEM_SELFTEST'                : 62, 
	'GET_DEVICE_INFO'                : 63, 
	'GET_DEVICE_INFO2'               : 64, 
	'INIT_LOG_TRANSMIT'              : 80, 
	'GET_LOG_PART'                   : 81, 
}


RemoteControlFunction = {
	'GET_PARAMETER_VALUE'          : 1,
	'SET_PARAMETER_VALUE'          : 2,
	'GET_PARAMETER_NAME'           : 3,
	'GET_PARAMETER_DESCRIPTION'    : 4,
	'GET_PARAMETER_MINIMUM_VALUE'  : 5,
	'GET_PARAMETER_MAXIMUM_VALUE'  : 6,
	'GET_PARAMETER_DEFAULT_VALUE'  : 7,
	'GET_PARAMETER_UNIT'           : 8,
}

RemoteControlSetParameterResult = {
	'SET_PARAMETER_STATUS_OK'    : 0,
	'SET_PARAMETER_STATUS_ERROR' : 1,
}

RemoteControlGetParameterResult = {
	'GET_PARAMETER_STATUS_OK'    : 0,
	'GET_PARAMETER_STATUS_ERROR' : 1,
}

TemperatureSourceFunction = {
	'REQUEST_TEMPERATURE' : 0,
	'GET_TEMPERATURE'     : 1,
	'GET_PROPERTIES'      : 2,
	'REQUEST_POWER'       : 3,
	'GET_CURRENT_POWER'   : 4,
	'GET_WORK_TIME'       : 5,
}

ConsumerFunction = {
	'GIVE_WAY'                   : 1,
	'PROCEED'                    : 2,
	'SET_COOLING'                : 3,
	'SET_WARM_UP'                : 4,
	'GET_REQUESTED_TEMPERATURE'  : 5,
}

HccFunction = {
	'STATE_1' : 0x01,
	'STATE_3' : 0x03,
	'MAPPING' : 0x0F,
}

CircuitFunction = {
	'RECEIVE_ROOM_STATUS' : 1,
}

ParameterSyncConfigFunction = {
	'epsc_connect'      : 0,        # data[0]: source data[1]:destination
	'epsc_factoryReset' : 1,        # reset all to defaults
	'epsc_roomCount'    : 2,        # tells other CALEONs number of rooms
	'epsc_roomSyncDone' : 3,        # there are at least as many rooms as CALEONs present
	'espc_setupWizard'  : 4,        # setup wizard synchronization between CALEONs
	'epsc_roomSyncStop' : 5,        # stop room sync
}


class SorelExfuncFunction:
	EF_VIRTUAL     = -3, # is used for flow animation
	EF_DISABLED    = -2
	EF_UNSELECTED  = -1

	EF_FIRST       = 0

	(EF_SOLARBYPASS,
	EF_HEIZEN,
	EF_HEIZEN2,
	EF_KUEHLEN,
	EF_RUECKLAUFANHEBUNG,
	EF_DISSIPATION,
	EF_ANTILEGIO,
	EF_UMLADUNG,
	EF_DIFFERENZ,
	EF_HOLZKESSEL) = range(0,10)

	(EF_SCHUTZFUNKTION,
	EF_DRUCKREGELUNG,
	EF_BOOSTER,
	EF_R1PARALLELBETRIEB,  # any relay parallel to R1
	EF_R2PARALLELBETRIEB,
	EF_DAUEREIN,
	EF_HEIZKREISRC21,
	EF_CIRCULATION,
	EF_STORAGEHEATING) = range(10, 19)
	(EF_HCCHEATREQUEST,
	EF_STORAGESTACKING) = range(EF_STORAGEHEATING, EF_STORAGEHEATING+2)
# old block fwc
	(EF_R_V1_PARALLEL,  # any relay parallel to V1
	EF_R_V2_PARALLEL,
	EF_R1_PERMANENTLY_ON,   # EF_DAUEREIN can only be used once, fwc use multiple functions
	EF_R2_PERMANENTLY_ON,
	EF_R3_PERMANENTLY_ON,
	EF_R_V3_PARALLEL,
	EF_V1_PERMANENTLY_ON,
	EF_V2_PERMANENTLY_ON) = range(20, 28)
# new block
	(EF_PARALLEL1,
	EF_PARALLEL2,
	EF_PARALLEL3,
	EF_PERMON1,
	EF_PERMON2,
	EF_PERMON3,
	EF_HC1_PUMP,            # heating circuit
	EF_HC2_PUMP,
	EF_EXTERNALALHEATING,
	EF_NEWLOGMESSAGE,

	EF_EXTRAPUMP,
	EF_PRIMARYMIXER_UP,
	EF_PRIMARYMIXER_DOWN,
	EF_SOLAR,
	EF_CASCADE,
	EF_DEHUMIDIFIER,
	EF_HEATINGROD,
	EF_THERMOSTAT,
	EF_DHW_VALVE,  # Brauchwasser Relais
	EF_BURNER,

	EF_COMPRESSOR,
	EF_BOILERPUMP,
	EF_LOADPUMP,
	EF_GLYCOLPUMP,
	EF_HEATEXCHANGER,
	EF_MIX1_UP,
	EF_MIX1_DOWN,
	EF_MIX2_UP,
	EF_MIX2_DOWN,
	EF_SOLARZONEVALVE,

	EF_SLUDGEPURGE,
	EF_REMOTERELAY1,
	EF_REMOTERELAY2,
	EF_REMOTERELAY3,
	EF_REMOTERELAY4,
	EF_RFI_MIX_UP,
	EF_RFI_MIX_DOWN,
	EF_TIMER1,
	EF_TIMER2,
	EF_TIMER3,

	EF_TIMER4,
	EF_VENTILATINGFAN,
	EF_HEATTRANSFER_REVERSE,
	EF_HEATTRANSFER_PUMP,
	EF_STORAGE_LAYER1,
	EF_STORAGE_LAYER2,
	EF_STORAGE_LAYER3,
	EF_COOLING_VALVE1,
	EF_COOLING_VALVE2,
	EF_FREE_COOLING,

	EF_GROUNDWATER_PUMP,
	EF_HEATCONTROL_PUMP,
	EF_HOTWATERSUPPLY, # normally a valve, same functionality as pump of fresh water controller, new for hcc_fresh
	EF_COLDREQUEST,    # for sdkV4 energyRequst will be used for heating and cooling

	EF_MAX) = range(20, 75)



RoomSyncConfigFunction = {
	SorelExfuncFunction.EF_UNSELECTED     : 'efid_unknown'       ,
	SorelExfuncFunction.EF_CIRCULATION    : 'efid_circulation'   ,
	SorelExfuncFunction.EF_DEHUMIDIFIER   : 'efid_dehumidifier'  ,
	SorelExfuncFunction.EF_DIFFERENZ      : 'efid_difference'    ,
	SorelExfuncFunction.EF_KUEHLEN        : 'efid_seasonSwitch'  ,
	SorelExfuncFunction.EF_DHW_VALVE      : 'efid_dhwValve'      ,
	SorelExfuncFunction.EF_HOTWATERSUPPLY : 'efid_hotwaterSupply',
	
	SorelExfuncFunction.EF_TIMER1    : 'efid_userTimer' ,  
	SorelExfuncFunction.EF_TIMER2    : 'efid_dhwTimer'  ,   # may be replaced by efid_userTimer (relay on/off only) or efid_dhwValve (release time)
	SorelExfuncFunction.EF_TIMER3    : 'efid_resTimer'  ,   # reserved
	SorelExfuncFunction.EF_TIMER4    : 'efid_timeSwitch',# master timer function
	SorelExfuncFunction.EF_HEIZEN    : 'efid_heatingCircuit' ,  # global settings of heating circuit module # pumps 
	SorelExfuncFunction.EF_HC1_PUMP  : 'efid_hcPump'         ,  # settings for each heating circuit
	SorelExfuncFunction.EF_HC2_PUMP  : 'efid_masterPump'     ,  
	SorelExfuncFunction.EF_EXTRAPUMP : 'efid_extraPump'      ,  
    
	SorelExfuncFunction.EF_MIX1_UP           : 'efid_mixer'            , # base function used by heating circuit  # mixer variants (handled in module mixer)
	SorelExfuncFunction.EF_MIX1_DOWN         : 'efid_mixerDown'        , # no function, optional relay for CAN
	SorelExfuncFunction.EF_MIX2_UP           : 'efid_resMixer'         , # reserved
	SorelExfuncFunction.EF_MIX2_DOWN         : 'efid_resMixerDown'     , # no function, optional relay for CAN
	SorelExfuncFunction.EF_PRIMARYMIXER_UP   : 'efid_primaryMixer'     , # variant for primary mixer (fresh water)
	SorelExfuncFunction.EF_PRIMARYMIXER_DOWN : 'efid_primaryMixerDown' , # no function, optional relay for CAN
	SorelExfuncFunction.EF_RFI_MIX_UP        : 'efid_rfiMixer'         , # variant for return flow increase mixer
	SorelExfuncFunction.EF_RFI_MIX_DOWN      : 'efid_rfiMixerDown'     , # no function, optional relay for CAN

	SorelExfuncFunction.EF_THERMOSTAT     : 'efid_thermostat'       ,    # thermostat variants (handled in module thermostat)  # base function 
	SorelExfuncFunction.EF_HEIZEN2        : 'efid_zone'             ,    # variant for zone valve
	SorelExfuncFunction.EF_VENTILATINGFAN : 'efid_ventilatingFan'   ,    # variant for fan

	SorelExfuncFunction.EF_HEIZKREISRC21 : 'efid_vhcData'         ,    # new for SDKv4
	SorelExfuncFunction.EF_REMOTERELAY2  : 'efid_energyRequest'   , 
	SorelExfuncFunction.EF_REMOTERELAY3  : 'efid_res1'            ,    # reserved
	SorelExfuncFunction.EF_REMOTERELAY4  : 'efid_res2'            ,    # reserved
	
	0 : 'AskForRooms',
}

Function = {
	'PROGRAM'            : ProgramFunction,
	'CONSUMER'           : ConsumerFunction,
	'TEMPERATURE_SOURCE' : TemperatureSourceFunction,
	'CONTROLLER'         : ControllerFunction,
	'REMOTE_CONTROL'     : RemoteControlFunction,
	'HCC'                : HccFunction,
	'CIRCUIT'            : CircuitFunction,
	
	'PARAMETERSYNCCONFIG': ParameterSyncConfigFunction,
	'ROOMSYNC'           : RoomSyncConfigFunction,
}

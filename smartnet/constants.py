
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
	'ID'                 : 0,                      
	'INPUT'              : 1,     
	'OUTPUT'             : 2,      
	'TITLE'              : 3,     
	'INPUT_MAPPING'      : 4,             
	'OUTPUT_MAPPING'     : 5,              
	'SCHEME'             : 6,      
	'TRAINING_ENABLED'   : 7,                
	'MANUAL_MODE_ENABLED': 8,                   
	'OUTPUT_MANUAL_STATE': 9,                   
}

ProgramScheme = {
	'DEFAULT' : 0,

	'CIRCUIT_MIXED'         : 0,
	'CIRCUIT_HEAT_EXCHANGE' : 1,
	'CIRCUIT_DIRECT'        : 2,
	'CIRCUIT_HEATING_LINE'  : 3,
}

RoomDeviceParameter = {                             
	'ROOM_COMFORT_TEMPERATURE'          :  1,
	'ROOM_REDUCED_TEMPERATURE'          :  2,
	'ROOM_HYSTERESIS'                   :  3,
	'RELAY_PERIOD'                      :  4,
	'RESPONSIBLE_CIRCUIT_1'             :  5,
	'RESPONSIBLE_CIRCUIT_2'             :  6,
	'RESPONSIBLE_CIRCUIT_3'             :  7,
	'WORK_MODE'                         :  8,
	'ROOM_DEVICE_VALVE_STATE'           :  9,
	'MINIMUM_FLOOR_TEMPERATURE'         : 10,
	'MAXIMUM_FLOOR_TEMPERATURE'         : 11,
	'RADIATOR_MINIMUM_SIGNAL'           : 12,
	'ROOM_DESIRED_TEMPERATURE'          : 13,
	'RELAY_PERCENTAGE_PRIMARY'          : 14,
	'RELAY_PERCENTAGE_SECONDARY'        : 15,
	'OUTDOOR_TEMPERATURE'               : 16,
	'RELAY_PERCENTAGE_ADDITIONAL'       : 17,
	'CIRCUIT_1_SHIFT'                   : 18,
	'CIRCUIT_2_SHIFT'                   : 19,
	'CIRCUIT_3_SHIFT'                   : 20,
	'ROOM_OFF_TEMPERATURE'              : 21,
	'SCHEDULE'                          : 22,
	'FLOOR_REQUIRED_TEMPERATURE'        : 23,
	'CURRENT_FLOOR_REQUIRED_TEMPERATURE': 24,
	'WALL_REQUIRED_TEMPERATURE'         : 25,
	'CURRENT_WALL_REQUIRED_TEMPERATURE' : 26,
	'HEAT_EXTRICATION'                  : 27,
	'FLOOR_REDUCED_TEMPERATURE'         : 28,
	'WALL_REDUCED_TEMPERATURE'          : 29,
	'CURRENT_WORK_MODE_STATUS'          : 30,
	'VENTILATION_CIRCUIT'               : 31,
	'REQUIRED_HUMIDITY'                 : 32,
	'POOL_CIRCUIT'                      : 33,
	'POOL_TEMPERATURE_OFFSET'           : 34,

	'SCHEDULE_2_0': 35,
	'LOCATION'    : 36,
}

ControllerParameter = {
	'SENSOR'                       :  1,
	'OUTPUT'                       :  2,
	'USED_SENSORS_MASK'            :  3,
	'USED_RELAYS_MASK'             :  4,
	'TITLE'                        :  5,
	'CONTROLLER_TYPE'              :  6,
	'REVISION'                     :  7,
	'INPUTS_MASK'                  :  8,
	'OUTPUTS_MASK'                 :  9,
	'ANALOG_INPUT_SIGNAL_TYPE'     : 10,
	'ANALOG_INPUT_SENSOR_TYPE'     : 11,
	'ANALOG_INPUT_POINT_X1'        : 12,
	'ANALOG_INPUT_POINT_Y1'        : 13,
	'ANALOG_INPUT_POINT_X2'        : 14,
	'ANALOG_INPUT_POINT_Y2'        : 15,
	'ANALOG_OUTPUT_PROFIL'         : 16,
	'ANALOG_OUTPUT_SIGNAL_FORM'    : 17,
	'ANALOG_OUTPUT_SIGNAL_AUS'     : 18,
	'ANALOG_OUTPUT_SIGNAL_EIN'     : 19,
	'ANALOG_OUTPUT_SIGNAL_MAX'     : 20,
	'ANALOG_OUTPUT_DREHZAH_BEI_EIN': 21,
	'ANALOG_OUTPUT_TYP'            : 22,
	'NETWORK_INPUT_CONFIG'         : 23,
	'NETWORK_VAR_INPUT_CONFIG'     : 24,
	'NETWORK_OUTPUT_CONFIG'        : 25,
	'VARIABLE_TYPE'                : 26,
	'OUTPUT_TO_VARIABLE_MAPPING'   : 27,
	'DATE'                         : 28,
	'TIME'                         : 29,
	'SENSOR_CALIBRATION'           : 30,
	'DISCRETTE_OUTPUT_SIGNAL_FORM' : 31,
	'ANALOG_OUTPUT_MAX_Y'          : 32,
	
	'SENSOR_TYPE'                  : 33,
	'SENSOR_INFO'                  : 34,

	'SUMMER_TIME_SWITCH'           : 35, 
	'TIME_MASTER'                  : 36,
	'ADAPTER_TYPE'                 : 37, 
	'ADAPTER_SPEED'                : 38, 
	'ADAPTER_PARITY'               : 39, 

	'CONTROLLER_ID'                : 40, 

	'ADAPTER_STOP_BIT_NUM'         : 41, 

	'RELAY_TEST_ENABLE'            : 42, 

	'OUTPUT_MANUAL_VALUE'          : 43, 
}


HeatingCircuitParameter = {
	'FROST_PROTECTION_TEMPERATURE'  :  1,
	'VALVE_RUNING_TIME'             :  2,
	'VALVE_OPEN_PROPORTIONAL_BAND'  :  3,
	'VALVE_CLOSE_PROPORTIONAL_BAND' :  4,
	'VALVE_BLOCK'                   :  5,
	'PUMP_MODE'                     :  6,
	'PUMP_OFF_OUTDOOR_TEMPERATURE'  :  7,
	'ANALOG_CICRULATION_PUMP_STATE' :  8,
	'ANALOG_HEATCHANGE_PUMP_STATE'  :  9,
	'VALVE_POSITION'                : 10,
}                       

CircuitParameter = {
		'REQUIRED_CONSTANT_FLOW_TEMPERATURE'                 :  1,
		'HEAT_CALCULATION_MODE'                              :  2,
		'HEATING_SLOPE'                                      :  3,
		'ROOM_SENSOR_INFLUENCE'                              :  4,
		'OUTDOOR_TEMPERATURE'                                :  5,
		'ANALOG_PUMP_CONTORL_MODE'                           :  6,
		'ANALOG_PUMP_MINIMUM_SPEED'                          :  7,
		'ANALOG_PUMP_CONSTANT_SPEED'                         :  8,
		'ROOM_SENSOR_INFLUENCE_MIN'                          :  9,
		'ROOM_SENSOR_INFLUENCE_MAX'                          : 10,
		'CURRENT_SUPPORTED_ROOM_DEVICE_TEMPERATURE'          : 11,
		'CURRENT_SUPPORTED_ROOM_DEVICE_REQUIRED_TEMPERATURE' : 12,
		'CURRENT_SUPPORTED_ROOM_DEVICE_ID'                   : 13,
		'OUTSIDE_TEMPERATURE_REQUEST_VALUE'                  : 14,
		'MINIMUM_FLOW_TEMPERATURE'                           : 15,
		'MAXIMUM_FLOW_TEMPERATURE'                           : 16,
		'ANALOG_PUMP_MAXIMUM_SPEED'                          : 17,
		'FLOW_CIRCULATION_IS_ACTIVE'                         : 18,
}

ConsumerParameter = {
	'PRIORITY'                  :  1,
	'GENERATOR_ID'              :  2,
	'DUMMY1'                    :  3,
	'DUMMY2'                    :  4,
	'TEMPERATURE_COMPENSATION'  :  5,
	'REQUIRED_TEMPERATURE'      :  6,
	'GENERATOR_TEMPERATURE'     :  7,
	'HEAT_EXTRICATION_ENABLED'  :  8,
}

SnowMelterParameter = {
	'WORK_MODE'                                               :  1,
	'MINIMUM_OUTDOOR_TEMPERATURE'                             :  2,
	'MAXIMUM_OUTDOOR_TEMPERATURE'                             :  3,
	'REQUIRED_CONSTANT_FLOW_TEMPERATURE_OF_SECONDARY_CIRCUIT' :  4,
	'OUTDOOR_TEMPERATURE'                                     :  5,
	'PRIMARY_CIRCUIT_PROTECTION_TEMPERATURE'                  :  6,
	'REQUIRED_PLATE_TEMPERATURE'                              :  7,
}

CascadeManagerParameter = {
	'PARAM_ROTATION_PERIOD'                        :  1,
	'PARAM_TEMPERATURE_SOURCE_ID'                  :  2,
	'PARAM_TEMPERATURE_SOURCE_TYPE'                :  3,
	'PARAM_TEMPERATURE_SOURCE_POWER'               :  4,
	'PARAM_TEMPERATURE_SOURCE_WORKTIME'            :  5,
	'PARAM_TEMPERATURE_SOURCE_PRIORITY'            :  6,
	'PARAM_P_FACTOR'                               :  7,
	'PARAM_I_FACTOR'                               :  8,
	'PARAM_D_FACTOR'                               :  9,
	'SCHEDULE'                                     : 10,
	'REQUIRED_POWER'                               : 11,
	'NEXT_TEMPERATURE_SRC_ON_DELAY'                : 12,
	'ROTATION_TYPE'                                : 13,
	'TEMPERATURE_OFFSET'                           : 14,
	'MINIMUM_REQUIRED_TEMPERATURE'                 : 15,
	'MAXIMUM_REQUIRED_TEMPERATURE'                 : 16,
	'WORK_FUNCTION'                                : 17,
	'TEMPERATURE_SOURCE_OFF_DELAY_BY_TEMPERATURE'  : 18,
}

CascadeManagerParameter = {
	'PARAM_ROTATION_PERIOD'                        :  1,
	'PARAM_TEMPERATURE_SOURCE_ID'                  :  2,
	'PARAM_TEMPERATURE_SOURCE_TYPE'                :  3,
	'PARAM_TEMPERATURE_SOURCE_POWER'               :  4,
	'PARAM_TEMPERATURE_SOURCE_WORKTIME'            :  5,
	'PARAM_TEMPERATURE_SOURCE_PRIORITY'            :  6,
	'PARAM_P_FACTOR'                               :  7,
	'PARAM_I_FACTOR'                               :  8,
	'PARAM_D_FACTOR'                               :  9,
	'SCHEDULE'                                     : 10,
	'REQUIRED_POWER'                               : 11,
	'NEXT_TEMPERATURE_SRC_ON_DELAY'                : 12,
	'ROTATION_TYPE'                                : 13,
	'TEMPERATURE_OFFSET'                           : 14,
	'MINIMUM_REQUIRED_TEMPERATURE'                 : 15,
	'MAXIMUM_REQUIRED_TEMPERATURE'                 : 16,
	'WORK_FUNCTION'                                : 17,
	'TEMPERATURE_SOURCE_OFF_DELAY_BY_TEMPERATURE'  : 18,
}

DistrictHeatingParameter = {
	'PARAM_VALVE_MIN'                              :  1,
	'PARAM_VALVE_RUNNING_TIME'                     :  2,
	'PARAM_P_FACTOR'                               :  3,
	'PARAM_I_FACTOR'                               :  4,
	'PARAM_D_FACTOR'                               :  5,
	'PARAM_BACKWARD_CONTROL_TYPE'                  :  6,
	'PARAM_SUPPLY_PUMP_CONTROL_TYPE'               :  7,
	'PARAM_MAXIMUM_BACKWARD_TEMPERATURE'           :  8,
	'PARAM_MAXIMUM_BACKWARD_TEMPERATURE_II'        :  9,
	'PARAM_OUTDOOR_TEMPERATURE_II'                 : 10,
	'PARAM_THERMAL_OUTPUT_CALIBRATION'             : 11,
	'PARAM_VOLUME_FLOW_CALIBRATION'                : 12,
	'PARAM_MAXIMUM_THERMAL_OUTPUT'                 : 13,
	'PARAM_MAXIMUM_VOLUME_FLOW'                    : 14,
	'PARAM_TEMPERATURE_SOURCE_POWER_REQUEST_DELAY' : 15,
	'PARAM_TEMPERATURE_SOURCE_ID'                  : 16,
	'PARAM_CURRENT_MAXIMUM_BACKWARD_TEMPERATURE'   : 17,
}

SwimmingPoolParameter = {
	'REQUIRED_POOL_TEMPERATURE'         :  1,
	'CURRENT_REQUIRED_POOL_TEMPERATURE' :  2,
	'WORK_MODE'                         :  3,
	'SCHEDULE'                          :  4,
	'CIRCULATION_PUMP_WORK_MODE'        :  5,
	'CIRCULATION_PUMP_WORK_PERIOD_ON'   :  6,
	'CIRCULATION_PUMP_WORK_PERIOD_OFF'  :  7,
	'REQUIRED_POOL_TEMPERATURE_ECONOM'  :  8,
	'FILLING_DURATION'                  :  9,
	'LOW_WATER_LEVEL_ALARM_RESET'       : 10,
	'CURRENT_WORK_MODE_STATUS'          : 11,
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

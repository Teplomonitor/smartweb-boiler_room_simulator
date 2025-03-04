
smartNetHeaderFlag = {
	0: 'Request',
	1: 'Response',
}

ControllerType = {
	 0: 'UNDEFINED',
	 1: 'STDC',
	 2: 'LTDC',
	 3: 'XHCC',
	 4: 'SWN',
	 5: 'SWD',
	 6: 'CALEON',
	 7: 'XHCC_S62',
	 8: 'LTDC_S45',
	 9: 'VIRTUAL',
	10: 'SWK',
	11: 'SWK_1',
	12: 'CWC_CAN',
	13: 'CALEON_RC50',
	14: 'EXT_CONTROLLER',
	15: 'CALEONBOX',
}

ProgramType = {
	 0: 'CAN_PROGRAM_TYPE_UNDEFINED',
	 1: 'PROGRAM',
	 2: 'OUTDOOR_SENSOR',
	 3: 'CONSUMER',
	 4: 'CASCADE_MANAGER',
	 5: 'ROOM_DEVICE',
	 6: 'TEMPERATURE_SOURCE',
	 7: 'HEAT_ACCUMULATOR',
	 8: 'EXTENDED_CONTROLLER',
	 9: 'EXTENSION_CONTROLLER',
	10: 'MONITORING_DEVICE',
	11: 'CONTROLLER',
	12: 'CIRCUIT',
	13: 'SCHEDULE',
	14: 'HEATING_CIRCUIT',
	15: 'DIRECT_CIRCUIT',
	16: 'DHW',
	17: 'FLOW_THROUGH_DHW',
	18: 'TEMPERATURE_GENERATOR',
	19: 'POOL',
	20: 'THERMOSTAT',
	21: 'SNOWMELT',
	22: 'REMOTE_CONTROL',
	23: 'BOILER',
	24: 'CHILLER',
	25: 'SOLAR_COLLECTOR',
	26: 'VENTILATION',
	27: 'GENERIC_RELAY',
	28: 'ALARM',
	29: 'FILLING_LOOP',
    
	0x80 : 'DATALOGGER_MONITOR',
	0x81 : 'EVENT',
	0x82 : 'FWC_CASCADE',             # freshwater controller cascading functions
	0x83 : 'DATALOGGER_NAMEDSENSORS', # request sensor values by name eg. outdor, room temperature/humidity, rc switch, or get changes
	0x84 : 'HCC',                     # heating circuit control program, eg. heat request
	0x85 : 'DL_CONFIGMENU_DATALOGGER',# datalogger configuration, receiver is datalogger                                                                          
	0x86 : 'DL_CONFIGMENU_CONTROLLER',# receiver is controller                                                                                                    
	0x87 : 'CLOCKSYNC',               # send/receive date and time                                                                                                
	0x88 : 'REMOTERELAY',             # set relay from external controller                                                                                        
	0x89 : 'HOLIDAYRETURNDATE',       # holiday return date                                                                                                       
	0x8A : 'DAYSCHEDULE',             # day schedule, function type is used to select day of the week, 0 = monday, 7 messages needed for week schedule            
	0x8B : 'AVAILABLERESOURCES',      # sending available resources (relays, sensors, ...) on request ore at startup                                              
	0x8C : 'PARAMETERSYNC',           # sending parameter values from one device to an other, parameter list / functionId is defined in exfuncIDs.h (teFunctionId)
	0x8D : 'RESOURCEDATA1WIRE',       # sending additional data of resource on request (1wire ROM data)                                                           
	0x8E : 'FILETRANSFER',            # send multiple can packets                                                                                                 
	0x8F : 'PARAMETERSYNCCONFIG',     # configuration for parameter sync, factory reset, ...                                                                      
	0x90 : 'ROOMSYNC',                # special PARAMETERSYNC for vhcData (no destination check)                                                                  
	0x91 : 'PANIC',                   # tells other controllers to slow down CAN packet transfer frequency                                                        
	0x92 : 'VHCDATA_UPDATE',          # function:0 broadcast last manual mode change                                                                              
	0x93 : 'MSGLOG',                  # global message log: Function = message severity, Data = [4 byte param1, 2 byte param2, 2 byte message code]

	0xC0 : 'CHARLIE',
}

ProgramParameter = {
	 0: 'ID',
	 1: 'INPUT',
	 2: 'OUTPUT',
	 3: 'TITLE',
	 4: 'INPUT_MAPPING',
	 5: 'OUTPUT_MAPPING',
	 6: 'SCHEME',
	 7: 'TRAINING_ENABLED',
	 8: 'MANUAL_MODE_ENABLED',
	 9: 'OUTPUT_MANUAL_STATE',
}

RoomDeviceParameter = {
	 1: 'ROOM_COMFORT_TEMPERATURE',
	 2: 'ROOM_REDUCED_TEMPERATURE',
	 3: 'ROOM_HYSTERESIS',
	 4: 'RELAY_PERIOD',
	 5: 'RESPONSIBLE_CIRCUIT_1',
	 6: 'RESPONSIBLE_CIRCUIT_2',
	 7: 'RESPONSIBLE_CIRCUIT_3',
	 8: 'WORK_MODE',
	 9: 'ROOM_DEVICE_VALVE_STATE',
	10: 'MINIMUM_FLOOR_TEMPERATURE',
	11: 'MAXIMUM_FLOOR_TEMPERATURE',
	12: 'RADIATOR_MINIMUM_SIGNAL',
	13: 'ROOM_DESIRED_TEMPERATURE',
	14: 'RELAY_PERCENTAGE_PRIMARY',
	15: 'RELAY_PERCENTAGE_SECONDARY',
	16: 'OUTDOOR_TEMPERATURE',
	17: 'RELAY_PERCENTAGE_ADDITIONAL',
	18: 'CIRCUIT_1_SHIFT',
	19: 'CIRCUIT_2_SHIFT',
	20: 'CIRCUIT_3_SHIFT',
	21: 'ROOM_OFF_TEMPERATURE',
	22: 'SCHEDULE',
	23: 'FLOOR_REQUIRED_TEMPERATURE',
	24: 'CURRENT_FLOOR_REQUIRED_TEMPERATURE',
	25: 'WALL_REQUIRED_TEMPERATURE',
	26: 'CURRENT_WALL_REQUIRED_TEMPERATURE',
	27: 'HEAT_EXTRICATION',
	28: 'FLOOR_REDUCED_TEMPERATURE',
	29: 'WALL_REDUCED_TEMPERATURE',
	30:	'CURRENT_WORK_MODE_STATUS',
	31:	'VENTILATION_CIRCUIT',
	32:	'REQUIRED_HUMIDITY',
	33:	'POOL_CIRCUIT',
	34:	'POOL_TEMPERATURE_OFFSET',

	35:	'SCHEDULE_2_0',
	36: 'LOCATION',
}

ControllerParameter = {
	 1: 'SENSOR',                   
	 2: 'OUTPUT',                       
	 3: 'USED_SENSORS_MASK',           
	 4: 'USED_RELAYS_MASK',             
	 5: 'TITLE',                        
	 6: 'CONTROLLER_TYPE',              
	 7: 'REVISION',                     
	 8: 'INPUTS_MASK',                  
	 9: 'OUTPUTS_MASK',                 
	10: 'ANALOG_INPUT_SIGNAL_TYPE',     
	11: 'ANALOG_INPUT_SENSOR_TYPE',     
	12: 'ANALOG_INPUT_POINT_X1',        
	13: 'ANALOG_INPUT_POINT_Y1',        
	14: 'ANALOG_INPUT_POINT_X2',        
	15: 'ANALOG_INPUT_POINT_Y2',        
	16: 'ANALOG_OUTPUT_PROFIL',         
	17: 'ANALOG_OUTPUT_SIGNAL_FORM',    
	18: 'ANALOG_OUTPUT_SIGNAL_AUS',     
	19: 'ANALOG_OUTPUT_SIGNAL_EIN',     
	20: 'ANALOG_OUTPUT_SIGNAL_MAX',     
	21: 'ANALOG_OUTPUT_DREHZAH_BEI_EIN',
	22: 'ANALOG_OUTPUT_TYP',            
	23: 'NETWORK_INPUT_CONFIG',      
	24: 'NETWORK_VAR_INPUT_CONFIG',  
	25: 'NETWORK_OUTPUT_CONFIG',     
	26: 'VARIABLE_TYPE',             
	27: 'OUTPUT_TO_VARIABLE_MAPPING',
	28: 'DATE',                        
	29: 'TIME',                        
	30:	'SENSOR_CALIBRATION',          
	31:	'DISCRETTE_OUTPUT_SIGNAL_FORM',
	32:	'ANALOG_OUTPUT_MAX_Y',
	
	33: 'SENSOR_TYPE',
	34: 'SENSOR_INFO',

	35: 'SUMMER_TIME_SWITCH',
	36: 'TIME_MASTER',

	37: 'ADAPTER_TYPE'  ,
	38: 'ADAPTER_SPEED' ,
	39: 'ADAPTER_PARITY',

	40: 'CONTROLLER_ID',

	41: 'ADAPTER_STOP_BIT_NUM',

	42: 'RELAY_TEST_ENABLE',
	
	43: 'OUTPUT_MANUAL_VALUE',
}


HeatingCircuitParameter = {
	 1: 'FROST_PROTECTION_TEMPERATURE',
	 2: 'VALVE_RUNING_TIME',
	 3: 'VALVE_OPEN_PROPORTIONAL_BAND',
	 4: 'VALVE_CLOSE_PROPORTIONAL_BAND',
	 5: 'VALVE_BLOCK',
	 6: 'PUMP_MODE',
	 7: 'PUMP_OFF_OUTDOOR_TEMPERATURE',
	 8: 'ANALOG_CICRULATION_PUMP_STATE',
	 9: 'ANALOG_HEATCHANGE_PUMP_STATE',
	10: 'VALVE_POSITION',
}


ParameterDict = {
	'PROGRAM'        : ProgramParameter,
	'ROOM_DEVICE'    : RoomDeviceParameter,
	'CONTROLLER'     : ControllerParameter,
	'HEATING_CIRCUIT': HeatingCircuitParameter,
}


ProgramFunction = {
	 1: 'IS_ID_OCCUPIED',
	 2: 'IS_TYPE_SUPPORTED',
	 3: 'GET_PROGRAM_TYPE',
	 4: 'GET_PROGRAM_NAME',
	 5: 'GET_PROGRAM_TYPES',
	 6: 'GET_SMARTNET_PROTOCOL_VERSION',
	 7: 'I_AM_PROGRAM',
	 8: 'IS_COLLISION',
	 9: 'MY_ID_CHANGED',
}



ControllerFunction = {
	 0: 'HAS_ANYBODY_HERE',
	 1: 'I_AM_HERE',
	 2: 'GET_CONTROLLER',
	 3: 'GET_ACTIVE_PROGRAMS_LIST',
	 4: 'ADD_NEW_PROGRAM',
	 5: 'REMOVE_PROGRAM',
	 6: 'GET_SYSTEM_DATE_TIME',
	 7: 'SET_SYSTEM_DATE_TIME',
	 8: 'GET_CONTROLLER_TYPE',
	 9: 'GET_PROGRAM_VERSION',
	10: 'GET_CHANNEL_NUMBER',
	11: 'GET_OUTPUT_TYPE',
	12: 'GET_INPUT_TYPE',
	13: 'GET_CHANNEL_BINDING',
	14: 'GET_INPUT_VALUE',
	15: 'SET_OUTPUT_VALUE',
	16: 'HAS_ERROR',
	17: 'GET_CONTROLLER_MASKS',
	18: 'GET_CHANNELS_INFO',
	19: 'GET_OUTPUT_VALUE',
	20: 'TIME_MASTER_IS_ACTIVE',

	21 : 'JOURNAL',

	22 : 'GET_VARIABLE',
	23 : 'SET_VARIABLE',

	24 : 'GET_RELAY_MAPPING',
	25 : 'SET_RELAY_MAPPING',

	26 : 'RESET_TO_DEFAULTS',
	27 : 'RESET_PROGRAMS',
	28 : 'MARK_JOURNAL_MESSAGES_AS_READ',
	
	
	40 : 'I_AM_RESETED',
	41 : 'DATALOGGER_TEST',
	
	42 : 'IS_ANYBODY_HERE_CAN2', # IS_ANYBODY_HERE that comes over CAN2 or is routed CAN2 -> CAN1
	43 : 'I_AM_HERE_CAN2',       # I_AM_HERE that comes over CAN2 or is routed CAN2 -> CAN1
	44 : 'I_AM_RESETED_CAN2',    # I_AM_RESETED that comes over CAN2 or is routed CAN2 -> CAN1
	
	
	
	60 : 'GET_FW_VERSION',
	61 : 'INSTALL_FW_UPDATE',
	62 : 'SYSTEM_SELFTEST',
	
	63 : 'GET_DEVICE_INFO',
	64 : 'GET_DEVICE_INFO2',
	
	80 : 'INIT_LOG_TRANSMIT',
	81 : 'GET_LOG_PART',
}


RemoteControlFunction = {
	 1: 'GET_PARAMETER_VALUE',
	 2: 'SET_PARAMETER_VALUE',
	 3: 'GET_PARAMETER_NAME',
	 4: 'GET_PARAMETER_DESCRIPTION',
	 5: 'GET_PARAMETER_MINIMUM_VALUE',
	 6: 'GET_PARAMETER_MAXIMUM_VALUE',
	 7: 'GET_PARAMETER_DEFAULT_VALUE',
	 8: 'GET_PARAMETER_UNIT',
}

TemperatureSourceFunction = {
	0: 'REQUEST_TEMPERATURE',
	1: 'GET_TEMPERATURE',
	2: 'GET_PROPERTIES',
	3: 'REQUEST_POWER',
	4: 'GET_CURRENT_POWER',
	5: 'GET_WORK_TIME',
}

ConsumerFunction = {
	1: 'GIVE_WAY',
	2: 'PROCEED',
	3: 'SET_COOLING',
	4: 'SET_WARM_UP',
	5: 'GET_REQUESTED_TEMPERATURE',
}

HccFunction = {
	0x01: 'STATE_1',
	0x03: 'STATE_3',
	0x0F: 'MAPPING',
}

CircuitFunction = {
	1: 'RECEIVE_ROOM_STATUS',
}

ParameterSyncConfigFunction = {
	0: 'epsc_connect',              # data[0]: source, data[1]:destination
	1: 'epsc_factoryReset',         # reset all to defaults
	2: 'epsc_roomCount',            # tells other CALEONs number of rooms
	3: 'epsc_roomSyncDone',         # there are at least as many rooms as CALEONs present
	4: 'espc_setupWizard',          # setup wizard synchronization between CALEONs
	5: 'epsc_roomSyncStop',         # stop room sync
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


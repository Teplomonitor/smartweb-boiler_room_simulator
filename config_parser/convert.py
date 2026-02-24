
import json

from smartnet.channelMapping import ChannelMapping as Mapping
from smartnet.constants      import ProgramType    as ProgramTypes
from smartnet.constants      import ParameterDict  as ParameterDict

typeDict = {
	0: 'CHANNEL_SENSOR_LOCAL' ,
	1: 'CHANNEL_RELAY_LOCAL'  ,
	2: 'CHANNEL_SENSOR'       ,
	3: 'CHANNEL_RELAY'        ,
	4: 'CHANNEL_INPUT'        ,
	5: 'CHANNEL_OUTPUT'       ,
	6: 'CHANNEL_RESERVED'     ,
	7: 'CHANNEL_UNDEFINED'    ,
}
	
host_controller_max_inputs  = 6
host_controller_max_outputs = 7

hostCommonTitle = 'HOST_'
hostCommonId    = 123
hostCommonType = 'SWK_1'
programCommonId = 101

def parseMappingValue(value):
	host = value[0]
	
	channelIdAndType = value[1]
	
	channelId = channelIdAndType & 0x1F
	channelType = channelIdAndType >> 5
	
	return Mapping(channelId, typeDict[channelType], host)

def parseParameterCode(code, parameterValue):
	bytes_val = code.to_bytes(2, byteorder='big')
	programType = bytes_val[0]
	parameterId = bytes_val[1]
	
	programTypeKey = None
	param          = None
	
	for key, value in ProgramTypes.items():
		if programType == value:
			programTypeKey = key
			break
		
	if programTypeKey in ParameterDict:
		params = ParameterDict[programTypeKey]
		for key, value in params.items():
			if parameterId == value:
				param = key
				break
	
	return {'type':programTypeKey, 'param':param, 'value':parameterValue}
	
	
def strToMapping(mappingValue):
	num = int(mappingValue)  
	bytes_val = num.to_bytes(2, byteorder='little')  
	
	return parseMappingValue(bytes_val)

def roundUp(value, maxValue):
	return int((value + maxValue - 1)/maxValue)

def computeControllersNum(parsed_programs):
	total_inputs  = 0
	total_outputs = 0
	for prg in parsed_programs:
		for programInput in prg['inputs']:
			if programInput.getChannelType() != 'CHANNEL_UNDEFINED':
				total_inputs += 1
				
		for programOutput in prg['outputs']:
			if programOutput.getChannelType() != 'CHANNEL_UNDEFINED':
				total_outputs += 1
				
	
	controller_required_num_1 = roundUp(total_inputs , host_controller_max_inputs)
	controller_required_num_2 = roundUp(total_outputs, host_controller_max_outputs)
	
	return max(controller_required_num_1, controller_required_num_2)
	

def getHeader():
	return '''
from smartnet.remoteControl import RemoteControlParameter as RemoteControlParameter
from smartnet.channelMapping import ChannelMapping as Mapping

import presets.preset

'''
def getFootter():
	return '''

def getPresetsList() :
	programPresetList = []
	for prg in programList:
		programPresetList.append(presets.preset.ProgramPreset(
			programType    [prg],
			programScheme  [prg],
			programId      [prg],
			programTitle   [prg],
			programSettings[prg],
			programInputs  [prg],
			programOutputs [prg],
			programPower   [prg],
			)
		)

	controllerPresetList = []
	for ctrl in hostList:
		controllerPresetList.append(presets.preset.ControllerPreset(
			hostType    [ctrl],
			hostId      [ctrl],
			hostTitle   [ctrl],
			)
		)

	return programPresetList, controllerPresetList

'''
	
	
	
programDefaultPower = {
	'BOILER'           :   3,
	'DISTRICT_HEATING' :   7,
	'CASCADE_MANAGER'  :   0,
	'OUTDOOR_SENSOR'   :   0,
	'SNOWMELT'         :  -2,
	'HEATING_CIRCUIT'  :  -2,
	'DHW'              :  -4,
	'ROOM_DEVICE'      :  -2,
	'POOL'             :  -2,
}


roomMandatoryParameter = 0


def getHostDeclaration(hostNum):
	output_string = 'hostList = [\n'
	for ctr in range(0, hostNum):
		output_string += f"'{hostCommonTitle}{ctr}',\n"
	output_string += ']\n\n'
	return output_string
	
def getHostId(hostNum):
	output_string = 'hostId = {\n'
	for ctr in range(0, hostNum):
		output_string += f"'{hostCommonTitle}{ctr}' : {hostCommonId+ctr},\n"
	output_string += '}\n\n'
	return output_string
	
def getHostType(hostNum):
	output_string = 'hostType = {\n'
	for ctr in range(0, hostNum):
		output_string += f"'{hostCommonTitle}{ctr}' : '{hostCommonType}',\n"
	output_string += '}\n\n'
	return output_string

def getHostTitle(hostNum):
	output_string = 'hostTitle = {\n'
	for ctr in range(0, hostNum):
		output_string += f"'{hostCommonTitle}{ctr}' : 'SWK_{hostCommonId+ctr}',\n"
	output_string += '}\n\n'
	return output_string

def getHostString(hostNum):
	output_string = ''
	output_string += getHostDeclaration(hostNum)
	output_string += getHostId         (hostNum)
	output_string += getHostType       (hostNum)
	output_string += getHostTitle      (hostNum)
	return output_string
	
def getProgramId(prg):
	return prg['id']

def getProgramDeclaration(programs):
	output_string = 'programList = {\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}',\t# {prg['title']}\n"
	output_string += '}\n\n'
	return output_string
	
def getProgramType(programs):
	output_string = 'programType = {\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}' : '{prg['type']}',\n"
	output_string += '}\n\n'
	return output_string

def convertProgramScheme(prg):
	if 'scheme' in prg:
		scheme_id = prg['scheme']
		return 'PROGRAM_SCHEME_' + scheme_id
	return 'DEFAULT'

def getProgramScheme(programs):
	output_string = 'programScheme = {\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}' : '{convertProgramScheme(prg)}',\n"
	output_string += '}\n\n'
	return output_string

def getProgramTitle(programs):
	output_string = 'programTitle = {\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}' : '{prg['title']}',\n"
	output_string += '}\n\n'
	return output_string

def getProgramIdArray(programs):
	programId = programCommonId
	output_string = 'programId = {\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}' : {programId},\n"
		programId += 1
	output_string += '}\n\n'
	return output_string

def getProgramSettings(programs):
	output_string = 'programSettings = {\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}' : [\n"
		for param in prg['parameters']:
			if (param['type'] != None) and (param['param'] != None):
				output_string += f"\tRemoteControlParameter('{param['type']}', '{param['param']}', '{param['value']}'),\n"
		output_string += '],\n'
	output_string += '}\n\n'
	return output_string

def getProgramInputs(programs):
	output_string = 'programInputs = {\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}' : [\n"
		for programChannel in prg['inputs']:
			channelType = programChannel.getChannelType()
			channelId   = programChannel.getChannelId()
			hostId      = programChannel.getHostId()
			
			if channelType == 'CHANNEL_SENSOR_LOCAL':
				channelType = 'CHANNEL_SENSOR' # make it remote
				channelId   = getProgramInputs.counter
				hostId      = hostCommonId + int(getProgramInputs.counter/host_controller_max_inputs)
				getProgramInputs.counter += 1
			
			output_string += f"\tMapping({channelId}, '{channelType}', {hostId}),\n"
		output_string += '],\n'
	output_string += '}\n\n'
	return output_string

getProgramInputs.counter = 0



def getProgramOutputs(programs):
	output_string = 'programOutputs = {\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}' : [\n"
		for programChannel in prg['outputs']:
			channelType = programChannel.getChannelType()
			channelId   = programChannel.getChannelId()
			hostId      = programChannel.getHostId()
			
			if channelType == 'CHANNEL_RELAY_LOCAL':
				channelType = 'CHANNEL_RELAY' # make it remote
				channelId   = getProgramOutputs.counter
				hostId      = hostCommonId + int(getProgramOutputs.counter/host_controller_max_outputs)
				getProgramOutputs.counter += 1
			
			output_string += f"\tMapping({channelId}, '{channelType}', {hostId}),\n"
		output_string += '],\n'
	output_string += '}\n\n'
	return output_string
getProgramOutputs.counter = 0

def getProgramPower(programs):
	output_string = 'programPower = {\n'
	for prg in programs:
		prgPower = 0
		if prg['type'] in programDefaultPower:
			prgPower = programDefaultPower[prg['type']]
		output_string += f"'{getProgramId(prg)}' : {prgPower},\n"
	output_string += '}\n\n'
	return output_string

def getProgramString(programs):
	output_string = ''
	output_string += getProgramDeclaration(programs)
	output_string += getProgramType       (programs)
	output_string += getProgramScheme     (programs)
	output_string += getProgramTitle      (programs)
	output_string += getProgramIdArray    (programs)
	output_string += getProgramSettings   (programs)
	output_string += getProgramInputs     (programs)
	output_string += getProgramOutputs    (programs)
	output_string += getProgramPower      (programs)
#	output_string += getHostType       (hostNum)
#	output_string += getHostTitle      (hostNum)
	return output_string
	
def convertConfigToPreset(json_string ):
	
	# Парсинг JSON в словарь Python
	try:
		data = json.loads(json_string)
	except ValueError:
		print('wrong config!')
		return ''
	
	programs = data['programs']
	
	parsed_programs = []
	
	for p in programs:
		for key, value in ProgramTypes.items():
			if int(p['type']) == value:
				new_program = {}
				new_program['type'   ] = key
				new_program['id'     ] = p['id']
				new_program['title'  ] = p['title']
				
				if new_program['title'] == '':
					new_program['title'] = new_program['type'] + '_' + str(new_program['id'])
				
				new_program['inputs' ] = []
				new_program['outputs'] = []
				new_program['parameters'] = []
				if 'parameters' in p:
					for param in p['parameters']:
						new_program['parameters'].append(parseParameterCode(param['code'], param['value']))
						
				for param in new_program['parameters']:
					if param['type'] == 'PROGRAM' and param['param'] == 'SCHEME':
						new_program['scheme' ] = param['value']
				
				for inputMapping in p['input_mappings']:
					new_program['inputs'].append(strToMapping(inputMapping))
					
				for outputMapping in p['output_mappings']:
					new_program['outputs'].append(strToMapping(outputMapping))
				
				parsed_programs.append(new_program)
				continue
	
	
	controller_required_num = computeControllersNum(parsed_programs)
	
	output_string = ''
	output_string += getHeader()
	output_string += getHostString(controller_required_num)
	output_string += getProgramString(parsed_programs)
	output_string += getFootter()

	
	
	
	return output_string 

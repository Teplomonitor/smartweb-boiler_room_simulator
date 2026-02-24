
import json

from smartnet.channelMapping import ChannelMapping as Mapping
from smartnet.constants      import ProgramType    as ProgramTypes

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
	
def parseMappingValue(value):
	host = value[0]
	
	channelIdAndType = value[1]
	
	channelId = channelIdAndType & 0x1F
	channelType = channelIdAndType >> 5
	
	return Mapping(channelId, typeDict[channelType], host)

def strToMapping(mappingValue):
	num = int(mappingValue)  
	bytes_val = num.to_bytes(2, byteorder='little')  
	
	return parseMappingValue(bytes_val)

def roundUp(value, maxValue):
	return int((value + maxValue - 1)/maxValue)

def computeControllersNum(inputs, outputs):
	controller_max_inputs  = 6
	controller_max_outputs = 7
	
	controller_required_num_1 = roundUp(inputs , controller_max_inputs)
	controller_required_num_2 = roundUp(outputs, controller_max_outputs)
	
	return max(controller_required_num_1, controller_required_num_2)
	

def getHeader():
	return '''
	
from presets.mapping import inputMapping  as inputMapping
from presets.mapping import outputMapping as outputMapping

'''

hostCommonTitle = 'HOST_'
hostCommonId    = 123
hostCommonType = 'SWK_1'

def getHostDeclaration(hostNum):
	output_string = 'hostList = [\n'
	for ctr in range(0, hostNum):
		output_string += f"'{hostCommonTitle}{ctr}',\n"
	output_string += ']\n'
	return output_string
	
def getHostId(hostNum):
	output_string = 'hostId = [\n'
	for ctr in range(0, hostNum):
		output_string += f"'{hostCommonTitle}{ctr}' : {hostCommonId+ctr},\n"
	output_string += ']\n'
	return output_string
	
def getHostType(hostNum):
	output_string = 'hostType = [\n'
	for ctr in range(0, hostNum):
		output_string += f"'{hostCommonTitle}{ctr}' : '{hostCommonType}',\n"
	output_string += ']\n'
	return output_string

def getHostTitle(hostNum):
	output_string = 'hostTitle = [\n'
	for ctr in range(0, hostNum):
		output_string += f"'{hostCommonTitle}{ctr}' : 'SWK_{hostCommonId+ctr}',\n"
	output_string += ']\n'
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
	output_string = 'programList = [\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}',\n"
	output_string += ']\n'
	return output_string
	
def getProgramType(programs):
	output_string = 'programType = [\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}' : '{prg['type']}',\n"
	output_string += ']\n'
	return output_string

def getProgramScheme(programs):
	output_string = 'programScheme = [\n'
	for prg in programs:
		output_string += f"'{getProgramId(prg)}' : '{prg['scheme']}',\n"
	output_string += ']\n'
	return output_string

def getProgramString(programs):
	output_string = ''
	output_string += getProgramDeclaration(programs)
	output_string += getProgramType       (programs)
	output_string += getProgramScheme     (programs)
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
				new_program['inputs' ] = []
				new_program['outputs'] = []
				for param in p['parameters']:
					if param['code'] == 262:
						new_program['scheme' ] = param['value']
						break
				
				for inputMapping in p['input_mappings']:
					new_program['inputs'].append(strToMapping(inputMapping))
					
				for outputMapping in p['output_mappings']:
					new_program['outputs'].append(strToMapping(outputMapping))
				
				parsed_programs.append(new_program)
				continue
	
	
	total_inputs  = 0
	total_outputs = 0
	for prg in parsed_programs:
		for programInput in prg['inputs']:
			if programInput.getChannelType() != 'CHANNEL_UNDEFINED':
				total_inputs += 1
				
		for programOutput in prg['outputs']:
			if programOutput.getChannelType() != 'CHANNEL_UNDEFINED':
				total_outputs += 1
	
	controller_required_num = computeControllersNum(total_inputs, total_outputs)
	
	output_string = ''
	output_string += getHeader()
	output_string += getHostString(controller_required_num)
	output_string += getProgramString(parsed_programs)

	
	
	
	return output_string 


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
				new_program['type'] = key
				new_program['id'] = int(p['id'])
				new_program['title'] = p['title']
				new_program['inputs']  = []
				new_program['outputs'] = []
				
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
	
	output_string = '''
	
from presets.mapping import inputMapping  as inputMapping
from presets.mapping import outputMapping as outputMapping

'''
	
	
	output_string += 'hostList = [\n'
	for ctr in range(0, controller_required_num):
		output_string += f"'HOST_{ctr+1}',\n"
	output_string += ']\n'
	
	
	return output_string 

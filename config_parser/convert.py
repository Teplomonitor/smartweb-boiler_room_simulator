"""
Configuration parser for converting JSON config to Python preset format.

This module provides utilities to parse and transform controller configurations
from JSON format into Python preset definitions.
"""

import json
from typing import Any, Dict, List, Optional, Union

from smartnet.channelMapping import ChannelMapping as Mapping
import smartnet.parameter_registry as param_registry

# Channel type mappings
CHANNEL_TYPE_MAP = {
	0: 'CHANNEL_SENSOR_LOCAL',
	1: 'CHANNEL_RELAY_LOCAL',
	2: 'CHANNEL_SENSOR',
	3: 'CHANNEL_RELAY',
	4: 'CHANNEL_INPUT',
	5: 'CHANNEL_OUTPUT',
	6: 'CHANNEL_RESERVED',
	7: 'CHANNEL_UNDEFINED',
}

# Controller constraints
HOST_CONTROLLER_MAX_INPUTS = 6
HOST_CONTROLLER_MAX_OUTPUTS = 7

# Controller naming and identification
HOST_COMMON_TITLE = 'HOST_'
HOST_COMMON_ID = 123
HOST_COMMON_TYPE = 'SWK_1'

# Channel type constants for sensor and relay filtering
SENSOR_CHANNEL_TYPES = {'CHANNEL_SENSOR_LOCAL', 'CHANNEL_SENSOR'}
RELAY_CHANNEL_TYPES = {'CHANNEL_RELAY_LOCAL', 'CHANNEL_RELAY'}

def parse_mapping_value(value: List[int]) -> Mapping:
	"""
	Parse a mapping value into a Mapping object.
	
	Args:
		value: List containing [host, channelIdAndType]
	
	Returns:
		Mapping object with decoded channel info
	"""
	host = value[0]
	channel_id_and_type = value[1]
	
	channel_id = channel_id_and_type & 0x1F
	channel_type = channel_id_and_type >> 5
	
	return Mapping(channel_id, CHANNEL_TYPE_MAP[channel_type], host)


def parse_parameter_code(code: int, parameter_value: Union[str, int]) -> Dict[str, Any]:
	"""
	Parse parameter code and value into structured parameter dictionary.
	
	Args:
		code: Parameter code as integer
		parameter_value: Parameter value (string or numeric)
	
	Returns:
		Dictionary with programType, parameterId, and parsed value
	"""
	bytes_val = code.to_bytes(2, byteorder='big')
	program_type_byte = bytes_val[0]
	parameter_id_byte = bytes_val[1]
	
	
	program_type = int(program_type_byte)
	parameter_id = int(parameter_id_byte)
	
	# Try to parse value as JSON, fall back to raw value
	try:
		parsed_value = json.loads(parameter_value)
	except (ValueError, TypeError):
		parsed_value = parameter_value
	
	return {
		'programType': program_type,
		'parameterId': parameter_id,
		'value': parsed_value
	}


def str_to_mapping(mapping_value: str) -> Mapping:
	"""
	Convert string representation of mapping to Mapping object.
	
	Args:
		mapping_value: String representation of mapping value
	
	Returns:
		Mapping object
	"""
	num = int(mapping_value)
	bytes_val = num.to_bytes(2, byteorder='little')
	return parse_mapping_value(bytes_val)


def round_up(value: int, max_value: int) -> int:
	"""
	Round up value to nearest multiple of max_value.
	
	Args:
		value: Value to round up
		max_value: Divisor for rounding
	
	Returns:
		Rounded up value
	"""
	return int((value + max_value - 1) / max_value)

def compute_controllers_num(parsed_programs: List[Dict[str, Any]]) -> int:
	"""
	Compute the number of controllers needed based on I/O counts.
	
	Args:
		parsed_programs: List of parsed program dictionaries
	
	Returns:
		Number of controllers required
	"""
	total_inputs = 0
	total_outputs = 0
	
	for program in parsed_programs:
		for program_input in program['inputs']:
			if program_input.get_channel_type() in SENSOR_CHANNEL_TYPES:
				total_inputs += 1
		
		for program_output in program['outputs']:
			if program_output.get_channel_type() in RELAY_CHANNEL_TYPES:
				total_outputs += 1
	
	controllers_for_inputs = round_up(total_inputs, HOST_CONTROLLER_MAX_INPUTS)
	controllers_for_outputs = round_up(total_outputs, HOST_CONTROLLER_MAX_OUTPUTS)
	
	return max(controllers_for_inputs, controllers_for_outputs)
	

def get_header() -> str:
	"""
	Generate the header for the generated preset file.
	
	Returns:
		Python code header as string
	"""
	return '''# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with main_config_parser.py
##
##
###########################################################################

import smartnet.remoteControl as rc
from smartnet.channelMapping import ChannelMapping as Mapping

import presets.preset
import presets.settings as ps

'''


def get_footer() -> str:
	"""
	Generate the footer for the generated preset file.
	
	Returns:
		Python code footer as string
	"""
	return '''
def get_presets_list():
	"""Generate and return presets lists for programs and controllers."""
	program_preset_list = []
	for prg in programList:
		program_preset_list.append(presets.preset.ProgramPreset(
			programType    [prg],
			programScheme  [prg],
			programId      [prg],
			programTitle   [prg],
			programSettings[prg],
			programInputs  [prg],
			programOutputs [prg],
		))

	controller_preset_list = []
	for ctrl in hostList:
		controller_preset_list.append(presets.preset.ControllerPreset(
			hostType [ctrl],
			hostId   [ctrl],
			hostTitle[ctrl],
		))

	return program_preset_list, controller_preset_list

'''
def get_host_declaration(host_num: int) -> str:
	"""
	Generate host list declaration.
	
	Args:
		host_num: Number of hosts to generate
	
	Returns:
		Python code for hostList
	"""
	lines = ['hostList = [']
	for host_idx in range(host_num):
		lines.append(f"'{HOST_COMMON_TITLE}{host_idx}',")
	lines.append(']\n\n')
	return '\n'.join(lines)


def get_host_id_dict(host_num: int) -> str:
	"""
	Generate host ID dictionary.
	
	Args:
		host_num: Number of hosts
	
	Returns:
		Python code for hostId dictionary
	"""
	lines = ['hostId = {']
	for host_idx in range(host_num):
		lines.append(f"'{HOST_COMMON_TITLE}{host_idx}': {HOST_COMMON_ID + host_idx},")
	lines.append('}\n\n')
	return '\n'.join(lines)


def get_host_type_dict(host_num: int) -> str:
	"""
	Generate host type dictionary.
	
	Args:
		host_num: Number of hosts
	
	Returns:
		Python code for hostType dictionary
	"""
	lines = ['hostType = {']
	for host_idx in range(host_num):
		lines.append(f"'{HOST_COMMON_TITLE}{host_idx}': '{HOST_COMMON_TYPE}',")
	lines.append('}\n\n')
	return '\n'.join(lines)


def get_host_title_dict(host_num: int) -> str:
	"""
	Generate host title dictionary.
	
	Args:
		host_num: Number of hosts
	
	Returns:
		Python code for hostTitle dictionary
	"""
	lines = ['hostTitle = {']
	for host_idx in range(host_num):
		lines.append(f"'{HOST_COMMON_TITLE}{host_idx}': 'SWK_{HOST_COMMON_ID + host_idx}',")
	lines.append('}\n\n')
	return '\n'.join(lines)


def get_host_string(host_num: int) -> str:
	"""
	Generate complete host configuration.
	
	Args:
		host_num: Number of hosts
	
	Returns:
		Complete Python code for all host definitions
	"""
	return (
		get_host_declaration(host_num) +
		get_host_id_dict(host_num) +
		get_host_type_dict(host_num) +
		get_host_title_dict(host_num)
	)
def get_program_id(program: Dict[str, Any]) -> Union[str, int]:
	"""
	Extract program ID from program dictionary.
	
	Args:
		program: Program dictionary
	
	Returns:
		Program ID
	"""
	return program['id']


def get_program_declaration(programs: List[Dict[str, Any]]) -> str:
	"""
	Generate program list declaration.
	
	Args:
		programs: List of program dictionaries
	
	Returns:
		Python code for programList
	"""
	lines = ['programList = {']
	for program in programs:
		prog_id = get_program_id(program)
		lines.append(f"'{prog_id}',\t# {program['title']}")
	lines.append('}\n\n')
	return '\n'.join(lines)


def get_program_type_dict(programs: List[Dict[str, Any]]) -> str:
	"""
	Generate program type dictionary.
	
	Args:
		programs: List of programs
	
	Returns:
		Python code for programType dictionary
	"""
	lines = ['programType = {']
	for program in programs:
		prog_id = get_program_id(program)
		lines.append(f"'{prog_id}': {program['type']},")
	lines.append('}\n\n')
	return '\n'.join(lines)


def convert_program_scheme(program: Dict[str, Any]) -> str:
	"""
	Convert program scheme to scheme identifier.
	
	Args:
		program: Program dictionary
	
	Returns:
		Scheme identifier string
	"""
	if 'scheme' in program:
		scheme_id = program['scheme']
		return f'PROGRAM_SCHEME_{scheme_id}'
	return 'DEFAULT'


def get_program_scheme_dict(programs: List[Dict[str, Any]]) -> str:
	"""
	Generate program scheme dictionary.
	
	Args:
		programs: List of programs
	
	Returns:
		Python code for programScheme dictionary
	"""
	lines = ['programScheme = {']
	for program in programs:
		prog_id = get_program_id(program)
		lines.append(f"'{prog_id}': '{convert_program_scheme(program)}',")
	lines.append('}\n\n')
	return '\n'.join(lines)


def get_program_title_dict(programs: List[Dict[str, Any]]) -> str:
	"""
	Generate program title dictionary.
	
	Args:
		programs: List of programs
	
	Returns:
		Python code for programTitle dictionary
	"""
	lines = ['programTitle = {']
	for program in programs:
		prog_id = get_program_id(program)
		lines.append(f"'{prog_id}': '{program['title']} {prog_id}',")
	lines.append('}\n\n')
	return '\n'.join(lines)


def get_program_id_dict(programs: List[Dict[str, Any]]) -> str:
	"""
	Generate program ID dictionary.
	
	Args:
		programs: List of programs
	
	Returns:
		Python code for programId dictionary
	"""
	lines = ['programId = {']
	for program in programs:
		prog_id = get_program_id(program)
		lines.append(f"'{prog_id}': {prog_id},")
	lines.append('}\n\n')
	return '\n'.join(lines)

def param_is_string(param: Dict[str, Any]) -> bool:
	"""
	Check if parameter is a string type.
	
	Args:
		param: Parameter dictionary
	
	Returns:
		True if parameter is string type
	"""
	return param_registry.is_string(param['programType'], param['parameterId'])


def param_is_array(param: Dict[str, Any]) -> bool:
	"""
	Check if parameter is an array type.
	
	Args:
		param: Parameter dictionary
	
	Returns:
		True if parameter is array type with size > 1
	"""
	return param_registry.is_array(param['programType'], param['parameterId'])


def get_parameter_setting_string(param: Dict[str, Any], value: Any) -> str:
	"""
	Generate parameter setting string for single parameter.
	
	Args:
		param: Parameter dictionary
		value: Parameter value
	
	Returns:
		Formatted parameter setting string
	"""
	if param_is_string(param):
		value = f"'{value}'"
	return f"\trc.RemoteControlParameter({param['programType']}, {param['parameterId']}, {value}),\n"


def get_parameter_array_setting_string(param: Dict[str, Any], value: Any, index: int) -> str:
	"""
	Generate parameter setting string for array parameter.
	
	Args:
		param: Parameter dictionary
		value: Array element value
		index: Array index
	
	Returns:
		Formatted parameter setting string with index
	"""
	if param_is_string(param):
		value = f"'{value}'"
	return f"\trc.RemoteControlParameter({param['programType']}, {param['parameterId']}, {value}, {index}),\n"


def get_program_settings_dict(programs: List[Dict[str, Any]]) -> str:
	"""
	Generate program settings dictionary.
	
	Args:
		programs: List of programs
	
	Returns:
		Python code for programSettings dictionary
	"""
	lines = ['programSettings = {']
	for program in programs:
		prog_id = get_program_id(program)
		lines.append(f"'{prog_id}': ps.DefaultSettings([")
		
		for param in program.get('parameters', []):
			if param['programType'] is not None and param['parameterId'] is not None:
				value = param['value']
				
				if param_is_array(param):
					for idx, v in enumerate(value):
						lines.append(get_parameter_array_setting_string(param, v, idx).rstrip('\n'))
				else:
					lines.append(get_parameter_setting_string(param, value).rstrip('\n'))
		
		lines.append(']),')
	lines.append('}\n\n')
	return '\n'.join(lines)

class ChannelCounter:
	"""Helper class to manage channel allocation across controllers."""
	
	def __init__(self, max_channels: int):
		"""
		Initialize channel counter.
		
		Args:
			max_channels: Maximum channels per controller
		"""
		self.counter = 0
		self.max_channels = max_channels
	
	def allocate_channel(self) -> tuple[int, int]:
		"""
		Allocate next channel and return (channel_id, controller_id).
		
		Returns:
			Tuple of (channel_id, host_id)
		"""
		channel_id = self.counter % self.max_channels
		controller_offset = self.counter // self.max_channels
		host_id = HOST_COMMON_ID + controller_offset
		self.counter += 1
		return channel_id, host_id
	
	def reset(self):
		"""Reset counter to 0."""
		self.counter = 0


def get_program_inputs_dict(programs: List[Dict[str, Any]]) -> str:
	"""
	Generate program inputs dictionary.
	
	Args:
		programs: List of programs
	
	Returns:
		Python code for programInputs dictionary
	"""
	lines = ['programInputs = {']
	input_counter = ChannelCounter(HOST_CONTROLLER_MAX_INPUTS)
	
	for program in programs:
		prog_id = get_program_id(program)
		lines.append(f"'{prog_id}': [")
		
		for program_channel in program.get('inputs', []):
			channel_type = program_channel.get_channel_type()
			channel_id = program_channel.get_channel_id()
			host_id = program_channel.get_host_id()
			
			if channel_type in SENSOR_CHANNEL_TYPES:
				channel_type = 'CHANNEL_SENSOR'  # Make it remote
				channel_id, host_id = input_counter.allocate_channel()
			
			lines.append(f"\tMapping({channel_id}, '{channel_type}', {host_id}),")
		
		lines.append('],')
	
	lines.append('}\n\n')
	return '\n'.join(lines)


def get_program_outputs_dict(programs: List[Dict[str, Any]]) -> str:
	"""
	Generate program outputs dictionary.
	
	Args:
		programs: List of programs
	
	Returns:
		Python code for programOutputs dictionary
	"""
	lines = ['programOutputs = {']
	output_counter = ChannelCounter(HOST_CONTROLLER_MAX_OUTPUTS)
	
	for program in programs:
		prog_id = get_program_id(program)
		lines.append(f"'{prog_id}': [")
		
		for program_channel in program.get('outputs', []):
			channel_type = program_channel.get_channel_type()
			channel_id = program_channel.get_channel_id()
			host_id = program_channel.get_host_id()
			
			if channel_type in RELAY_CHANNEL_TYPES:
				channel_type = 'CHANNEL_RELAY'  # Make it remote
				channel_id, host_id = output_counter.allocate_channel()
			
			lines.append(f"\tMapping({channel_id}, '{channel_type}', {host_id}),")
		
		lines.append('],')
	
	lines.append('}\n\n')
	return '\n'.join(lines)

def get_program_string(programs: List[Dict[str, Any]]) -> str:
	"""
	Generate complete program configuration.
	
	Args:
		programs: List of program dictionaries
	
	Returns:
		Complete Python code for all program definitions
	"""
	return (
		get_program_declaration(programs) +
		get_program_type_dict(programs) +
		get_program_scheme_dict(programs) +
		get_program_title_dict(programs) +
		get_program_id_dict(programs) +
		get_program_settings_dict(programs) +
		get_program_inputs_dict(programs) +
		get_program_outputs_dict(programs)
	)
def convert_config_to_preset(json_string: str) -> str:
	"""
	Convert JSON configuration to Python preset format.
	
	Args:
		json_string: JSON configuration as string
	
	Returns:
		Python code containing preset definitions
	"""
	# Parse JSON into Python dictionary
	try:
		data = json.loads(json_string)
	except (ValueError, json.JSONDecodeError) as e:
		print(f'Error: Invalid JSON configuration - {e}')
		return ''
	
	programs = data.get('programs', [])
	parsed_programs = []
	
	# Parse each program configuration
	for program_config in programs:
		program_type_code = int(program_config['type'])
		
		# Initialize program structure
		program = {
			'type': program_type_code,
			'id': program_config['id'],
			'title': program_config['title'],
			'inputs': [],
			'outputs': [],
			'parameters': [],
		}
		
		# Generate title if empty
		if not program['title']:
			program['title'] = f"{program['type']}_{program['id']}"
		
		# Parse parameters
		for param_config in program_config.get('parameters', []):
			parsed_param = parse_parameter_code(
				param_config['code'],
				param_config['value']
			)
			program['parameters'].append(parsed_param)
		
		# Extract scheme from parameters if present
		for param in program['parameters']:
			if (param['programType'] == 'PROGRAM' and
				param['parameterId'] == 'SCHEME'):
				program['scheme'] = param['value']
				break
		
		# Parse input and output mappings
		for input_mapping in program_config.get('input_mappings', []):
			program['inputs'].append(str_to_mapping(input_mapping))
		
		for output_mapping in program_config.get('output_mappings', []):
			program['outputs'].append(str_to_mapping(output_mapping))
		
		parsed_programs.append(program)
	
	# Compute required number of controllers
	controller_required_num = compute_controllers_num(parsed_programs)
	
	# Generate complete preset code
	output = ''
	output += get_header()
	output += get_host_string(controller_required_num)
	output += get_program_string(parsed_programs)
	output += get_footer()
	
	return output 

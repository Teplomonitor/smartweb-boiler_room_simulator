'''
@author: admin
'''

import os
from copy import copy


import smartnet.constants as snc

import smartnet.remoteControl  as sr
import smartnet.message        as sm

from smartnet.channelMapping import InputChannel     as InputChannel
from smartnet.channelMapping import OutputChannel    as OutputChannel

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error

def input_info (channelId,
			title,
			minValue = 0,
			maxValue = 100,
			step     = 1,
			units    = '°C'):
	channel = InputChannel(
		channelId = channelId,
		title     = title,
		minValue  = minValue,
		maxValue  = maxValue,
		units     = units
		)
	channel.setStep(step)
	return channel
	
def output_info(channelId, title):
	return OutputChannel(
		channelId = channelId,
		title     = title
		)


class ParameterInfo(object):
	def __init__(self,
				programType,
				parameterId):
		self._programType = programType
		self._parameterId = parameterId
	
	def get_program_type(self): return self._programType
	def get_parameter_id(self): return self._parameterId

class Program(object):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return snc.ProgramType.PROGRAM
	
	def get_inputs_num (self): return len(self._inputs )
	def get_outputs_num(self): return len(self._outputs)
	
	def init_input_mappings(self, mappings):
		for i in range(len(mappings)):
			for channel in self._inputs.values():
				if channel.get_id() == i:
					channel.set_mapping(mappings[i])
					break
			
	def init_output_mappings(self, mappings):
		for i in range(len(mappings)):
			for channel in self._outputs.values():
				if channel.get_id() == i:
					channel.set_mapping(mappings[i])
					if channel.is_mapped():
						self.read_output(channel)
					break
	
	def init_inputs(self):
		pass
	
	def init_outputs(self):
		pass
	
	def init_gui_parameters(self):
		pass
	
	def __init__(self, preset):
		'''
		Constructor
		'''
		
		self._inputs  = {}
		self._outputs = {}
		self._parameters = {}
		
		self.init_inputs ()
		self.init_outputs()
		self.init_gui_parameters()
		
		self._preset = preset
		
		if preset:
			self.set_scheme(preset.get_scheme())
			self.set_id    (preset.get_id()    )
			self.set_title (preset.get_title() )
			
			self.init_input_mappings (preset.get_inputs ())
			self.init_output_mappings(preset.get_outputs())
		else:
			self.set_scheme('DEFAULT')
			self.set_id    (1)
			self.set_title ('Program')
			
			
		self.can_subscribe()
	
	def get_preset(self):
		return self._preset
	
	def get_max_power(self):
		if 'max_power' in self._parameters:
			return self._parameters['max_power'].get_value()
		return 0
	
	def get_max_flow_rate(self):
		if 'max_flow_rate' in self._parameters:
			return self._parameters['max_flow_rate'].get_value()
		return 0

	def clear(self):
		self.can_unsubscribe()
		self._inputs  = {}
		self._outputs = {}
		self._parameters = {}
		
	
	def can_subscribe(self):
		sm.CanListener.subscribe(self)
		
	def can_unsubscribe(self):
		sm.CanListener.unsubscribe(self)
		
	def __del__(self):
		self.can_unsubscribe()
		print(f'kill {self.get_title()}')
		
	def on_can_message_received(self, msg):
		headerOk = (
					(msg.getProgramId  () == self.get_id()) and
					(msg.get_program_type() == snc.ProgramType.REMOTE_CONTROL) and
					(msg.getFunctionId () == snc.RemoteControlFunction['GET_PARAMETER_VALUE']) and
					(msg.getRequestFlag() == snc.RequestFlag.RESPONSE))

		if headerOk:
			data   = msg.get_data()
			dataOk = (
				(data[0] == snc.ProgramType.PROGRAM) and
				(data[1] == snc.ProgramParameterId.OUTPUT))
			
			if dataOk:
				outputId    = data[2]
				outputValue = data[3]
				
				for out in self._outputs.values():
					if out.get_id() == outputId:
						out.set_value(outputValue)
						break
		
	def get_inputs (self): return self._inputs
	def get_outputs(self): return self._outputs
	
	def get_input_channel (self, channel): return self._inputs [channel]
	def get_output_channel(self, channel): return self._outputs[channel]
	
	def set_output_value   (self, channel, value): self.get_output_channel(channel).set_value(value)
	
	def get_parameters(self): return self._parameters
	
	def get_scheme   (self): return self._scheme
	def get_id       (self): return self._id
	def get_title    (self): return self._title
	
	def set_scheme(self, scheme   ): self._scheme = scheme
	def set_id    (self, programId): self._id     = programId
	def set_title (self, title    ): self._title  = title
	
	def get_gui_color (self): return 'default'

	def disable_gui_control(self):
		for prgInput in self._inputs.values():
			prgInput.disable_gui_control()
			
	def enable_gui_control(self):
		for prgInput in self._inputs.values():
			prgInput.enable_gui_control()
		
	def bind_input(self, channel_id, mapping):
		print_log(f'bind program input {channel_id}')
		def generate_request():
			request = sm.Message(
			snc.ProgramType.REMOTE_CONTROL,
			self.get_id(),
			snc.RemoteControlFunction.SET_PARAMETER_VALUE,
			snc.RequestFlag.REQUEST,
			[
				snc.ProgramType.PROGRAM,
				snc.ProgramParameterId.INPUT_MAPPING,
				channel_id,
				mapping.get_raw(0),
				mapping.get_raw(1)
			])
			return request

		def generate_required_response():
			response = copy(request)
			response.setRequestFlag(snc.RequestFlag.RESPONSE)
			return response

		def handle_response():
			if response is None:
				print_error('bind input timeout')
				return False
			else:
				data = response.get_data()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					print_log('bind ok!')
					return True
				else:
					print_error('bind error %d' %(result))
					return False
				
		
		request        = generate_request()
		responseFilter = generate_required_response()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 10)
			result = handle_response()
			if result:
				break
			print_log('retry')
			i = i + 1
			
		return result

	def bind_output(self, channel_id, mapping):
		print_log(f'bind program output {channel_id}')
		def generate_request():
			request = sm.Message(
			snc.ProgramType.REMOTE_CONTROL,
			self.get_id(),
			snc.RemoteControlFunction.SET_PARAMETER_VALUE,
			snc.RequestFlag.REQUEST,
			[
				snc.ProgramType.PROGRAM,
				snc.ProgramParameterId.OUTPUT_MAPPING,
				channel_id,
				mapping.get_raw(0),
				mapping.get_raw(1)
			])
			return request

		def generate_required_response():
			response = copy(request)
			response.setRequestFlag(snc.RequestFlag.RESPONSE)
			return response

		def handle_response():
			if response is None:
				print_error('bind output timeout')
				return False
			else:
				data = response.get_data()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					print_log('bind ok!')
					return True
				else:
					print_error('bind error %d' %(result))
					return False
				
		
		request        = generate_request()
		responseFilter = generate_required_response()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 10)
			result = handle_response()
			if result:
				break
			print_log('retry')
			i = i + 1
			
		return result
	
	def read_output(self, channel):
		param = sr.RemoteControlParameter(
			snc.ProgramType.PROGRAM, snc.ProgramParameterId.OUTPUT,
			parameterIndex = channel.get_id(),
			programId = self.get_id())
		
		value = None
		if param.read():
			value = param.get_value()
			channel.set_value(value)
			
		return value
	
	def get_parameter_info(self, parameter):
		return None
	
	def read_parameter_value(self, parameter):
		p = self.get_parameter_info(parameter)
		if p is None:
			return None
		remoteParam = sr.RemoteControlParameter(parameterInfo = p, programId = self.get_id() )
		remoteParam.read()
		
		return remoteParam.get_value()
	
	def write_parameter_value(self, parameter, value, index = None, confirm = True):
		p = self.get_parameter_info(parameter)
		if p is None:
			return None
		
		remoteParam = sr.RemoteControlParameter(
			parameterInfo = p,
			programId = self.get_id(),
			parameterValue = value,
			parameterIndex = index
		)
		
		remoteParam.write(confirm)
		
		return remoteParam.get_value()
	
	def save_log(self, logDir = None):
		titleCommon = self.get_title() + '_' + str(self.get_id())
		
		if logDir:
			titleCommon = os.path.join(logDir, titleCommon)
		
		logDirInputs  = os.path.join(titleCommon, 'inputs')
		logDirOutputs = os.path.join(titleCommon, 'outputs')
		
		for programInput in self._inputs.values():
			programInput.save_log(logDirInputs)
		for programOutput in self._outputs.values():
			programOutput.save_log(logDirOutputs)
	
	# TODO: move to derived consumer class
	def get_temperature_source(self):
		preset = self.get_preset()
		settings = preset.getSettings().get()
		for setting in settings:
			if setting.get_program_type() == snc.ProgramType.CONSUMER and setting.get_parameter_id_code() == 'GENERATOR_ID':
				return setting.get_value()
		return 0
	
	def get_temperature_source_list(self):
		return [self.get_temperature_source()]
	
	
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

from consoleLog import printLog   as printLog
from consoleLog import printError as printError

def InputInfo (channelId,
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
	
def OutputInfo(channelId, title):
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
	def get_type(): return 'PROGRAM'
	
	def get_inputs_num (self): return len(self._inputs )
	def get_outputs_num(self): return len(self._outputs)
	
	def init_input_mappings(self, mappings):
		for i in range(len(mappings)):
			for channel in self._inputs.values():
				if channel.get_id() == i:
					channel.setMapping(mappings[i])
					break
			
	def init_output_mappings(self, mappings):
		for i in range(len(mappings)):
			for channel in self._outputs.values():
				if channel.get_id() == i:
					channel.setMapping(mappings[i])
					if channel.isMapped():
						self.readOutput(channel)
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
			return self._parameters['max_power'].getValue()
		return 0
	
	def get_max_flow_rate(self):
		if 'max_flow_rate' in self._parameters:
			return self._parameters['max_flow_rate'].getValue()
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
					(msg.get_program_type() == snc.ProgramType['REMOTE_CONTROL']) and
					(msg.getFunctionId () == snc.RemoteControlFunction['GET_PARAMETER_VALUE']) and
					(msg.getRequestFlag() == snc.requestFlag['RESPONSE']))

		if headerOk:
			data   = msg.getData()
			dataOk = (
				(data[0] == snc.ProgramType['PROGRAM']) and
				(data[1] == snc.ProgramParameter['OUTPUT']['id']))
			
			if dataOk:
				outputId    = data[2]
				outputValue = data[3]
				
				for out in self._outputs.values():
					if out.get_id() == outputId:
						out.setValue(outputValue)
						break
		
	def get_inputs (self): return self._inputs
	def get_outputs(self): return self._outputs
	
	def get_input_channel (self, channel): return self._inputs [channel]
	def get_output_channel(self, channel): return self._outputs[channel]
	
	def set_output_value   (self, channel, value): self.get_output_channel(channel).setValue(value)
	
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
		printLog(f'bind program input {channel_id}')
		def generateRequest():
			request = sm.Message(
			snc.ProgramType['REMOTE_CONTROL'],
			self.get_id(),
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[
				snc.ProgramType['PROGRAM'],
				snc.ProgramParameter['INPUT_MAPPING']['id'],
				channel_id,
				mapping.getRaw(0),
				mapping.getRaw(1)
			])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse():
			if response is None:
				printError('bind input timeout')
				return False
			else:
				data = response.getData()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					printLog('bind ok!')
					return True
				else:
					printError('bind error %d' %(result))
					return False
				
		
		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 10)
			result = handleResponse()
			if result:
				break
			printLog('retry')
			i = i + 1
			
		return result

	def bind_output(self, channel_id, mapping):
		printLog(f'bind program output {channel_id}')
		def generateRequest():
			request = sm.Message(
			snc.ProgramType['REMOTE_CONTROL'],
			self.get_id(),
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[
				snc.ProgramType['PROGRAM'],
				snc.ProgramParameter['OUTPUT_MAPPING']['id'],
				channel_id,
				mapping.getRaw(0),
				mapping.getRaw(1)
			])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse():
			if response is None:
				printError('bind output timeout')
				return False
			else:
				data = response.getData()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					printLog('bind ok!')
					return True
				else:
					printError('bind error %d' %(result))
					return False
				
		
		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 10)
			result = handleResponse()
			if result:
				break
			printLog('retry')
			i = i + 1
			
		return result
	
	def readOutput(self, channel):
		param = sr.RemoteControlParameter(
			'PROGRAM', 'OUTPUT',
			parameterIndex = channel.get_id(),
			programId = self.get_id())
		
		value = None
		if param.read():
			value = param.getValue()
			channel.setValue(value)
			
		return value
	
	def getParameterInfo(self, parameter):
		return None
	
	def readParameterValue(self, parameter):
		p = self.getParameterInfo(parameter)
		if p is None:
			return None
		remoteParam = sr.RemoteControlParameter(parameterInfo = p, programId = self.get_id() )
		remoteParam.read()
		
		return remoteParam.getValue()
	
	def writeParameterValue(self, parameter, value, index = None, confirm = True):
		p = self.getParameterInfo(parameter)
		if p is None:
			return None
		
		remoteParam = sr.RemoteControlParameter(
			parameterInfo = p,
			programId = self.get_id(),
			parameterValue = value,
			parameterIndex = index
		)
		
		remoteParam.write(confirm)
		
		return remoteParam.getValue()
	
	def saveLog(self, logDir = None):
		titleCommon = self.get_title() + '_' + str(self.get_id())
		
		if logDir:
			titleCommon = os.path.join(logDir, titleCommon)
		
		logDirInputs  = os.path.join(titleCommon, 'inputs')
		logDirOutputs = os.path.join(titleCommon, 'outputs')
		
		for programInput in self._inputs.values():
			programInput.saveLog(logDirInputs)
		for programOutput in self._outputs.values():
			programOutput.saveLog(logDirOutputs)
	
	# TODO: move to derived consumer class
	def get_temperatureSource(self):
		preset = self.get_preset()
		settings = preset.getSettings().get()
		for setting in settings:
			if setting.get_program_type() == 'CONSUMER' and setting.get_parameter_idCode() == 'GENERATOR_ID':
				return setting.getValue()
		return 0
	
	def get_temperatureSourceList(self):
		return [self.get_temperatureSource()]
	
	
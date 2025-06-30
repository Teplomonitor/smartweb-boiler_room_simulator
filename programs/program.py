'''
@author: admin
'''

import os
from copy import copy

from simulator.outputRead    import outputRead       as outputRead

import smartnet.constants as snc

from smartnet.message        import CanListener      as CanListener
from smartnet.message        import Message          as smartnetMessage
from smartnet.channelMapping import InputChannel     as InputChannel
from smartnet.channelMapping import OutputChannel    as OutputChannel
from smartnet.channelTitle import ProgramInputTitle  as InputTitle
from smartnet.channelTitle import ProgramOutputTitle as OutputTitle

class Program(object):
	'''
	classdocs
	'''

	def __init__(self, preset):
		'''
		Constructor
		'''
		
		self._preset  = preset

		inputMappings  = preset.getInputs ().get()
		outputMappings = preset.getOutputs().get()

		self._inputs  = [InputChannel (mapping) for mapping in inputMappings ]
		self._outputs = [OutputChannel(mapping) for mapping in outputMappings]
	
		self._parameters = {}
		
		programId   = self.getId()
		prgType     = self.getType()
		inputTitle  = InputTitle [prgType]
		outputTitle = OutputTitle[prgType]
		
		i = 0
		for programInput in self._inputs:
			programInput.setTitle(inputTitle[i])
			i = i + 1

		i = 0
		for programOutput in self._outputs:
			programOutput.setTitle(outputTitle[i])
	
			mapping = programOutput.getMapping()
			if mapping:
				value = outputRead(programId, i)
				if value is None:
					print('cant read output value!!!')
				else:
					self.getOutput(i).setValue(value)
					
					
			i = i + 1
		
		CanListener.subscribe(self)
		
	def OnCanMessageReceived(self, msg):
		headerOk = (
					(msg.getProgramId  () == self.getId()) and
					(msg.getProgramType() == snc.ProgramType['REMOTE_CONTROL']) and
					(msg.getFunctionId () == snc.RemoteControlFunction['GET_PARAMETER_VALUE']) and
					(msg.getRequestFlag() == snc.requestFlag['RESPONSE']))

		if headerOk:
			data   = msg.getData()
			dataOk = (
				(data[0] == snc.ProgramType['PROGRAM']) and
				(data[1] == snc.ProgramParameter['OUTPUT']))
			
			if dataOk:
				outputId    = data[2]
				outputValue = data[3]
				self.getOutput(outputId).setValue(outputValue)
		
		
	def getInputs(self   ): return self._inputs
	def getInput (self, i): return self._inputs [i]
	def setInput (self, i, value): self._inputs [i] = value
	
	def getOutputs(self   ): return self._outputs
	def getOutput (self, i): return self._outputs[i]
	def setOutput (self, i, value): self._outputs[i] = value
	
	def getParameters(self): return self._parameters
	
	def getInputTitle (self, i): return self.getInput (i).getTitle()
	def getOutputTitle(self, i): return self.getOutput(i).getTitle()

	def getType     (self): return self._preset.getType()
	def getScheme   (self): return self._preset.getScheme()
	def getId       (self): return self._preset.getId()
	def getTitle    (self): return self._preset.getTitle()
	def getPreset   (self): return self._preset
	def getGuiColor (self): return 'default'

	def bindInput(self, channel_id, mapping):
		print(f'bind program input {channel_id}')
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			self.getId(),
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[snc.ProgramType['PROGRAM'], snc.ProgramParameter['INPUT_MAPPING'], channel_id, mapping.getRaw(0), mapping.getRaw(1)])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse():
			if response is None:
				print('bind input timeout')
				return False
			else:
				data = response.getData()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					print('bind ok!')
					return True
				else:
					print('bind error %d' %(result))
					return False
				
		
		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 10)
			result = handleResponse()
			if result:
				break;
			print('retry')
			i = i + 1
			
		return result

	def bindOutput(self, channel_id, mapping):
		print(f'bind program output {channel_id}')
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			self.getId(),
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[snc.ProgramType['PROGRAM'], snc.ProgramParameter['OUTPUT_MAPPING'], channel_id, mapping.getRaw(0), mapping.getRaw(1)])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse():
			if response is None:
				print('bind output timeout')
				return False
			else:
				data = response.getData()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					print('bind ok!')
					return True
				else:
					print('bind error %d' %(result))
					return False
				
		
		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 10)
			result = handleResponse()
			if result:
				break;
			print('retry')
			i = i + 1
			
		return result

	def setInputsRange(self, inputsRange):
		i = 0
		for inputRange in inputsRange:
			if inputRange:
				self._inputs[i].setMin(inputRange[0])
				self._inputs[i].setMax(inputRange[1])
			i = i + 1

	def saveLog(self):
		titleCommon = self.getTitle() + '_' + str(self.getId())
		
		logDirInputs  = os.path.join(titleCommon, 'inputs')
		logDirOutputs = os.path.join(titleCommon, 'outputs')
		
		for programInput in self._inputs:
			programInput.saveLog(logDirInputs)
		for programOutput in self._outputs:
			programOutput.saveLog(logDirOutputs)
	
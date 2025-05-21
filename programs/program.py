'''
@author: admin
'''

from copy import copy

import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage
from smartnet.channelMapping import Channel as Channel
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
		
		self._type    = preset.getType()
		self._id      = preset.getId()
		self._scheme  = preset.getScheme()
		self._title   = preset.getTitle()
		self._preset  = preset

		inputMappings  = preset.getInputs ().get()
		outputMappings = preset.getOutputs().get()

		self._inputs  = [Channel(mapping) for mapping in inputMappings ]
		self._outputs = [Channel(mapping) for mapping in outputMappings]
	
		self._inputTitle  = InputTitle[self._type]
		self._outputTitle = OutputTitle[self._type]
		
		i = 0
		for programInput in self._inputs:
			programInput.setTitle(self._inputTitle[i])
			i = i + 1

		i = 0
		for programOutput in self._outputs:
			programOutput.setTitle(self._outputTitle[i])
			i = i + 1

	def getInputs(self   ): return self._inputs
	def getInput (self, i): return self._inputs [i]
	def setInput (self, i, value): self._inputs [i] = value
	
	def getOutputs(self   ): return self._outputs
	def getOutput (self, i): return self._outputs[i]
	def setOutput (self, i, value): self._outputs[i] = value
	
	def getInputTitle (self, i): return self._inputTitle [i]
	def getOutputTitle(self, i): return self._outputTitle[i]

	def getType     (self): return self._type
	def getScheme   (self): return self._scheme
	def getId       (self): return self._id
	def getTitle    (self): return self._title
	def getPreset   (self): return self._preset

	def bindInput(self, channel_id, mapping):
		print(f'bind program input {channel_id}')
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			self._id,
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
			self._id,
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

		
	
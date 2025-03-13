'''
@author: admin
'''

from copy import copy

import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage

class Channel(object):
	'''
	classdocs
	'''

	def __init__(self, mapping = None, value = None):
		'''
		Constructor
		'''
		self._mapping = mapping
		self._value   = value

	def getMapping(self): return self._mapping
	def getValue  (self): return self._value

	def setMapping(self, mapping): self._mapping = mapping
	def setValue  (self, value  ): self._value   = value


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

		self._inputs  = [Channel(mapping, None) for mapping in inputMappings ]
		self._outputs = [Channel(mapping, None) for mapping in outputMappings]
	
	def getInputs(self   ): return self._inputs
	def getInput (self, i): return self._inputs [i]
	def setInput (self, i, value): self._inputs [i] = value

	def getOutput(self, i): return self._outputs[i]
	def setOutput(self, i, value): self._outputs[i] = value

	def getType     (self): return self._type
	def getScheme   (self): return self._scheme
	def getId       (self): return self._id
	def getTitle    (self): return self._title
	def getPreset   (self): return self._preset

	def bindInput(self, id, mapping):
		print(f'bind program input {id}')
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			self._id,
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[snc.ProgramType['PROGRAM'], snc.ProgramParameter['INPUT_MAPPING'], id, mapping.getRaw(0), mapping.getRaw(1)])
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

		response = request.send(responseFilter, 10)

		return handleResponse()

	

	def bindOutput(self, id, mapping):
		print(f'bind program output {id}')
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			self._id,
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[snc.ProgramType['PROGRAM'], snc.ProgramParameter['OUTPUT_MAPPING'], id, mapping.getRaw(0), mapping.getRaw(1)])
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

		response = request.send(responseFilter, 10)

		return handleResponse()

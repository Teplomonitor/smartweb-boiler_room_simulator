'''
@author: admin
'''

from copy import copy

import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage

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
		self._inputs  = [None] * 10
		self._outputs = [0] * 10
	
	def getInput (self, i): return self._inputs [i]
	def setInput (self, i, value): self._inputs [i] = value
	
	def getOutput(self, i): return self._outputs[i]
	def setOutput(self, i, value): self._outputs[i] = value

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


		pass
	

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

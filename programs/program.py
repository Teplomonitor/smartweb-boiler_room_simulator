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

	def __init__(self, programType, programId, programScheme = snc.ProgramScheme['DEFAULT']):
		'''
		Constructor
		'''
		
		self._type    = programType
		self._id      = programId
		self._scheme  = programScheme
		self._title   = None
		self._inputs  = []
		self._outputs = []
	
	def bindInput(self, inputId, mapping):
		print(f'bind program input {inputId}')
		def generateRequest(inputId, mapping):
			request = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			self._id,
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[snc.ProgramType['PROGRAM'], snc.ProgramParameter['INPUT_MAPPING'], inputId, mapping.getRaw(0), mapping.getRaw(1)])
			return request

		def generateRequiredResponse(request):
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse(response):
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


		request        = generateRequest(inputId, mapping)
		responseFilter = generateRequiredResponse(request)

		response = request.send(responseFilter, 10)

		return handleResponse(response)


		pass
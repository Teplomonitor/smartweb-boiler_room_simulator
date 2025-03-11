
from copy import copy

import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage

class RemoteControlParameter(object):
	def __init__(self,
		programType   ,
		parameterId   ,
		parameterValue,
		parameterIndex = None):
		self._programType    = programType   
		self._parameterId    = parameterId
		self._parameterValue = parameterValue
		self._parameterIndex = parameterIndex

	def getValue(self): return self._parameterValue

	def write(self, programId):
		if self._parameterIndex is None:
			print(f'prg {self._parameterId} write parameter {self._programType}.{self._parameterId} = {self._parameterValue}')
		else:
			print(f'prg {self._parameterId} write parameter {self._programType}.{self._parameterId}.{self._parameterIndex} = {self._parameterValue}')

		def generateRequest():

			if self._parameterIndex is None:
				data = [self._programType, self._parameterId, self._parameterValue]
			else:
				data = [self._programType, self._parameterId, self._parameterIndex, self._parameterValue]

			request = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			programId,
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			data)
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse():
			if response is None:
				print('write timeout')
				return False
			else:
				data = response.getData()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					print('write ok!')
					return True
				else:
					print('write error %d' %(result))
					return False

		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		response = request.send(responseFilter, 10)

		return handleResponse()



class HeatingCircuitSettings(object):
	def __init__(self,
			source         = None,
			):
		self._source         = source

	def get(self):
		return [
			RemoteControlParameter(
				snc.ProgramType['CONSUMER'], 
				snc.ConsumerParameter['GENERATOR_ID'], 
				self._source),
		]

class DhwSettings(object):
	def __init__(self,
			source         = None,
			):
		self._source         = source

	def get(self):
		return [
			RemoteControlParameter(
				snc.ProgramType['CONSUMER'], 
				snc.ConsumerParameter['GENERATOR_ID'], 
				self._source),
		]

class CascadeSettings(object):
	def __init__(self,
			source_1 = None,
			source_2 = None,
			source_3 = None,
			source_4 = None,
			source_5 = None,
			source_6 = None,
			source_7 = None,
			source_8 = None,
			):

		self._sourceList = [
			source_1,
			source_2,
			source_3,
			source_4,
			source_5,
			source_6,
			source_7,
			source_8,
			]

	def get(self):
		result = []
		i = 0
		for source in self._sourceList:
			if source:
				result.append(
					RemoteControlParameter(
						snc.ProgramType['CONSUMER'], 
						snc.ConsumerParameter['GENERATOR_ID'], 
						source, i)
				)
			i = i + 1

		return result

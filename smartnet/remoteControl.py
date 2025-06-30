
from copy import copy

import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage



def concatByteArray(data, littleEndian = False):
	value = 0
	i = 0
	
	if littleEndian:
		data = reversed(data)
	
	for b in data:
		value += b << (i*8)
		i+=1
		
	return value

def bytesToTemp(data, littleEndian = False):
	value = concatByteArray(data, littleEndian)
	
	if value == 0x8003: return 'UNDEF'
	if value == 0x8001: return 'SHORT'
	if value == 0x8002: return 'OPEN'
	
	value = value/10.0
	
	return value

class RemoteControlParameter(object):
	def __init__(self,
		programType   ,
		parameterId   ,
		parameterValue = None,
		parameterIndex = None,
		parameterType  = 'UINT8_T'):
		self._programType    = programType   
		self._parameterId    = parameterId
		self._parameterValue = parameterValue
		self._parameterIndex = parameterIndex
		self._parameterType  = parameterType

	def getValue(self): return self._parameterValue

	def write(self, programId):
		if self._parameterValue is None:
			print(f'prg {programId} skip parameter {self._programType}.{self._parameterId}')
			return
		
		if self._parameterIndex is None:
			print(f'prg {programId} write parameter {self._programType}.{self._parameterId} = {self._parameterValue}')
		else:
			print(f'prg {programId} write parameter {self._programType}.{self._parameterId}.{self._parameterIndex} = {self._parameterValue}')

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

		i = 0
		while i < 3:
			response = request.send(responseFilter, 10)
			result = handleResponse()
			if result:
				break;
			print('retry')
			i = i + 1
			
		return result
	
	def read(self, programId):
		if self._parameterIndex is None:
			print(f'prg {programId} read parameter {self._programType}.{self._parameterId}')
		else:
			print(f'prg {programId} read parameter {self._programType}.{self._parameterId}.{self._parameterIndex}')

		def generateRequest():
			if self._parameterIndex is None:
				data = [self._programType, self._parameterId]
			else:
				data = [self._programType, self._parameterId, self._parameterIndex]

			request = smartnetMessage(
				snc.ProgramType['REMOTE_CONTROL'],
				programId,
				snc.RemoteControlFunction['GET_PARAMETER_VALUE'],
				snc.requestFlag['REQUEST'],
				data)
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse():
			if response is None:
				print('read timeout')
				return False
			else:
				data = response.getData()
				
				if self._parameterIndex is None:
					valuePos = 2
				else:
					valuePos = 3
				
				valueSize = self.getParameterSize()
				int_array = [byte for byte in data]
				data_cut = int_array[valuePos:valuePos+valueSize]
				self._parameterValue = self.dataToValue(data_cut)
				
#				print('read ok!')
				return True

		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 3)
			result = handleResponse()
			if result:
				break;
			print('retry')
			i = i + 1
			
		return result
	
	def responseGet(self, programId):
		if self._parameterIndex is None:
			data = [self._programType, self._parameterId, self._parameterValue]
		else:
			data = [self._programType, self._parameterId, self._parameterIndex, self._parameterValue]

		response = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			programId,
			snc.RemoteControlFunction['GET_PARAMETER_VALUE'],
			snc.requestFlag['RESPONSE'],
			data)
		
		response.send()
		
	def getParameterSize(self):
		if self._parameterType == 'UINT8_T'    : return 1
		if self._parameterType == 'TEMPERATURE': return 2
		
	def dataToValue(self, data):
		if self._parameterType == 'UINT8_T'    : return data[0]
		if self._parameterType == 'TEMPERATURE': return bytesToTemp(data)

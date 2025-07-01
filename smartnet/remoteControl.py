
from copy import copy

import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage

from gui.frame import printLog   as printLog
from gui.frame import printError as printError


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
		parameterType  = 'UINT8_T',
		programId      = None
		):
		self._programType    = programType   
		self._parameterId    = parameterId
		self._parameterValue = parameterValue
		self._parameterIndex = parameterIndex
		self._parameterType  = parameterType
		self._programId      = programId

	def setProgramId(self, programId):
		self._programId      = programId
		
	def getValue(self): return self._parameterValue

	def getParameterIdCode(self):
		return snc.ParameterDict[self._programType][self._parameterId]
	
	def write(self):
		if self._programId is None:
			printError('wrong programId')
			return
		
		if self._parameterValue is None:
#			print(f'prg {self._programId} skip parameter {self._programType}.{self._parameterId}')
			return
		
		if self._parameterIndex is None:
			actionStr = f'prg {self._programId} write parameter {self._programType}.{self._parameterId} = {self._parameterValue}'
		else:
			actionStr = f'prg {self._programId} write parameter {self._programType}.{self._parameterId}.{self._parameterIndex} = {self._parameterValue}'

		def generateRequest():
			parameterIdCode = self.getParameterIdCode()
			if self._parameterIndex is None:
				data = [snc.ProgramType[self._programType], parameterIdCode, self._parameterValue]
			else:
				data = [snc.ProgramType[self._programType], parameterIdCode, self._parameterIndex, self._parameterValue]

			request = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			self._programId,
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
				printError(f'{actionStr}: write timeout')
				return False
			else:
				data = response.getData()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					return True
				else:
					printError(f'{actionStr}: write error {result}')
					return False

		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 3)
			result = handleResponse()
			if result:
				break;
			printLog(f'{actionStr}: retry')
			i = i + 1
			
		return result
	
	def read(self):
		if self._programId is None:
			printError('wrong programId')
			return
		
		if self._parameterIndex is None:
			actionStr = f'prg {self._programId} read parameter {self._programType}.{self._parameterId}'
		else:
			actionStr = f'prg {self._programId} read parameter {self._programType}.{self._parameterId}.{self._parameterIndex}'

		def generateRequest():
			parameterIdCode = self.getParameterIdCode()
			
			if self._parameterIndex is None:
				data = [snc.ProgramType[self._programType], parameterIdCode]
			else:
				data = [snc.ProgramType[self._programType], parameterIdCode, self._parameterIndex]

			request = smartnetMessage(
				snc.ProgramType['REMOTE_CONTROL'],
				self._programId,
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
				printError(f'{actionStr}: read timeout')
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
			printLog(f'{actionStr}: retry')
			i = i + 1
			
		return result
	
	def getParameterSize(self):
		if self._parameterType == 'UINT8_T'    : return 1
		if self._parameterType == 'TEMPERATURE': return 2
		
	def dataToValue(self, data):
		if self._parameterType == 'UINT8_T'    : return data[0]
		if self._parameterType == 'TEMPERATURE': return bytesToTemp(data)

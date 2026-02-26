
from copy import copy

import smartnet.constants as snc
import smartnet.message as sm

from consoleLog import printLog   as printLog
from consoleLog import printError as printError


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
	
	if value > 0x8000:
		value -= 0x10000
	
	value /= 10.0
	
	return value

def bytesToTdpFloat(data, littleEndian = False):
	value = concatByteArray(data, littleEndian)
	value /= 100.0
	
	return value
	
def tempToData(value, littleEndian = False):
	if value == 'UNDEF': return 0x8003
	if value == 'SHORT': return 0x8001
	if value == 'OPEN' : return 0x8002
	
	if isinstance(value, str):
		value = float(value)
	
	
	return int(value * 10)

def tdpFloatToData(value, littleEndian = False):
	if isinstance(value, str):
		value = float(value)
		
	return int(value * 100)
	
def timeToData(value, littleEndian = False):
	return value*1000

def schedulePeriodToData(value, littleEndian = False):
	start = int(value[0] / 60)
	stop  = int(value[1] / 60)
	data  = start | stop << 16
	return data

def bytesToInt(data, littleEndian = False):
	value = concatByteArray(data, littleEndian)
	return value

def bytesToTime(data, littleEndian = False):
	value = bytesToInt(data, littleEndian)
	value /=1000
	return value

def bytesToSchedulePeriod(data, littleEndian = False):
	start = bytesToInt(data[0:2], littleEndian)
	stop  = bytesToInt(data[2:4], littleEndian)
	return [start*60, stop*60]
	

class RemoteControlParameter(object):
	'''
		parameterType - value type used in CANBUS data transfer.
		Can be 
		'UINT8_T'    : 1 byte value, unsigned
		'TEMPERATURE': 2 byte value, used mostly for temperature. Value x10
		'TIME_MS'    : 4 byte value, used for time parameters. Milliseconds
		'SCHEDULE'   : table parameter (day, period). One table element - 4 bytes: 2 bytes - period start, 2 bytes - end (in minutes).
		'TDP_FLOAT'  : two decimal places float value x100. Used mostly for heating slope
	'''
	def __init__(self,
		programType    = None,
		parameterId    = None,
		parameterValue = None,
		parameterIndex = None,
		programId      = None,
		parameterInfo  = None
		):
		if parameterInfo:
			self._programType   = parameterInfo['programType']
			self._parameterId   = parameterInfo['parameter']
		else:
			self._programType    = programType   
			self._parameterId    = parameterId
			
		self._parameterValue = parameterValue
		self._parameterIndex = parameterIndex
		self._programId      = programId

	def setProgramId(self, programId): self._programId = programId
	
	def getValue         (self): return self._parameterValue
	def getProgramType   (self): return self._programType
	def getParameterIndex(self): return self._parameterIndex
	
	def getParameterIdCode(self): return snc.ParameterDict[self._programType][self._parameterId]['id']
	def getParameterType  (self): return snc.ParameterDict[self._programType][self._parameterId]['type']
	
	def getParameterArraySize(self):
		param = snc.ParameterDict[self._programType][self._parameterId]
		if 'array_size' in param:
			return param['array_size']
		return 1
	
	def write(self):
		if self._programId is None:
			printError('wrong programId')
			return
		
		if self._parameterValue is None:
#			print(f'prg {self._programId} skip parameter {self._programType}.{self._parameterId}')
			return
		
		#not supported yet
		if self.getParameterType() == 'STRING':
			return
		if self.getParameterType() == 'SCHEDULE':
			return
		
		if self._parameterIndex is None:
			actionStr = f'prg {self._programId} write parameter {self._programType}.{self._parameterId} = {self._parameterValue}'
		else:
			actionStr = f'prg {self._programId} write parameter {self._programType}.{self._parameterId}.{self._parameterIndex} = {self._parameterValue}'

		print(actionStr)
		
		def generateRequest():
			parameterIdCode = self.getParameterIdCode()
			
			parameterValue = self.valueToData(self._parameterValue)
			
			if self._parameterIndex is None:
				data = [snc.ProgramType[self._programType], parameterIdCode]
			else:
				data = [snc.ProgramType[self._programType], parameterIdCode, self._parameterIndex]
			
			data.extend(parameterValue)
			
			request = sm.Message(
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

			request = sm.Message(
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
		parameterType = self.getParameterType()
		if   parameterType == 'UINT8_T'    : return 1
		elif parameterType == 'TEMPERATURE': return 2
		elif parameterType == 'TIME_MS'    : return 4
		elif parameterType == 'SCHEDULE'   : return 4
		elif parameterType == 'TDP_FLOAT'  : return 2
		return 1
		
	def dataToValue(self, data):
		parameterType = self.getParameterType()
		if   parameterType == 'UINT8_T'    : return data[0]
		elif parameterType == 'TEMPERATURE': return bytesToTemp(data)
		elif parameterType == 'TIME_MS'    : return bytesToTime(data)
		elif parameterType == 'SCHEDULE'   : return bytesToSchedulePeriod(data)
		if   parameterType == 'TDP_FLOAT'  : return bytesToTdpFloat(data)
		return data[0]
		
	def valueToData(self, value):
		parameterType = self.getParameterType()
		data = value
		signedValue = False
		if   parameterType == 'UINT8_T'    : data = int(value)
		elif parameterType == 'TEMPERATURE': data = tempToData(value); signedValue = True
		elif parameterType == 'TIME_MS'    : data = timeToData(value)
		elif parameterType == 'SCHEDULE'   : data = schedulePeriodToData(value)
		elif parameterType == 'TDP_FLOAT'  : data = tdpFloatToData(value)
		
		parameterSize = self.getParameterSize()
		data_bytes = data.to_bytes(parameterSize, 'little', signed = signedValue)
		
		return list(data_bytes)

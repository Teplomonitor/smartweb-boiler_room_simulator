
from copy import copy

import smartnet.constants as snc
import smartnet.message as sm
import smartnet.parameter_registry as param_registry

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error


ParameterSize =  {
	'UINT8_T'    : 1,
	'UINT16_T'   : 2,
	'TEMPERATURE': 2,
	'TIME_MS'    : 4,
	'SCHEDULE'   : 4,
	'TDP_FLOAT'  : 2,
}


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
	return int(value*1000)

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
			self._programType   = parameterInfo.get_program_type()
			self._parameterId   = parameterInfo.get_parameter_id()
		else:
			self._programType    = programType
			self._parameterId    = parameterId
			
		self._parameterValue = parameterValue
		self._parameterIndex = parameterIndex
		self._programId      = programId

	def setProgramId(self, programId): self._programId = programId
	
	def get_value            (self): return self._parameterValue
	def get_program_type     (self): return self._programType
	def get_parameter_id_code(self): return self._parameterId
	def getParameterIndex    (self): return self._parameterIndex
	
	def getParameterType(self):
		param_def = param_registry.get_parameter(self._programType, self._parameterId)
		return param_def.type if param_def else None
	
	def getParameterArraySize(self):
		param_def = param_registry.get_parameter(self._programType, self._parameterId)
		return param_def.array_size if param_def else 1
	
	def write(self, confirm = True):
		if self._programId is None:
			print_error('wrong programId')
			return False
		
		if self._parameterValue is None:
#			print(f'prg {self._programId} skip parameter {self._programType}.{self._parameterId}')
			return False
		
		#not supported yet
		if self.getParameterType() == 'STRING':
			return False
		if self.getParameterType() == 'SCHEDULE':
			return False
		
		if self._parameterIndex is None:
			actionStr = f'prg {self._programId} write parameter {self._programType}.{self._parameterId} = {self._parameterValue:.2f}'
		else:
			actionStr = f'prg {self._programId} write parameter {self._programType}.{self._parameterId}.{self._parameterIndex} = {self._parameterValue:.2f}'

#		print(actionStr)
		
		def generate_request():
			parameterIdCode = self.get_parameter_id_code()
			
			parameterValue = self.valueToData(self._parameterValue)
			
			if self._parameterIndex is None:
				data = [self._programType, parameterIdCode]
			else:
				data = [self._programType, parameterIdCode, self._parameterIndex]
			
			data.extend(parameterValue)
			
			request = sm.Message(
			snc.ProgramType.REMOTE_CONTROL,
			self._programId,
			snc.RemoteControlFunction.SET_PARAMETER_VALUE,
			snc.RequestFlag.REQUEST,
			data)
			return request

		def generate_required_response():
			response = copy(request)
			response.setRequestFlag(snc.RequestFlag.RESPONSE)
			return response

		def handle_response():
			if response is None:
				print_error(f'{actionStr}: write timeout')
				return False
			else:
				data = response.get_data()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					return True
				else:
					print_error(f'{actionStr}: write error {result}')
					return False

		request = generate_request()
		
		if confirm == False:
			request.send()
			return True
		
		responseFilter = generate_required_response()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 3)
			result = handle_response()
			if result:
				break;
			print_log(f'{actionStr}: retry')
			i = i + 1
			
		return result
	
	def read(self):
		if self._programId is None:
			print_error('wrong programId')
			return False
		
		if self._parameterIndex is None:
			actionStr = f'prg {self._programId} read parameter {self._programType}.{self._parameterId}'
		else:
			actionStr = f'prg {self._programId} read parameter {self._programType}.{self._parameterId}.{self._parameterIndex}'

		def generate_request():
			parameterIdCode = self.get_parameter_id_code()
			
			if self._parameterIndex is None:
				data = [self._programType, parameterIdCode]
			else:
				data = [self._programType, parameterIdCode, self._parameterIndex]

			request = sm.Message(
				snc.ProgramType.REMOTE_CONTROL,
				self._programId,
				snc.RemoteControlFunction.GET_PARAMETER_VALUE,
				snc.RequestFlag.REQUEST,
				data)
			return request

		def generate_required_response():
			response = copy(request)
			response.setRequestFlag(snc.RequestFlag.RESPONSE)
			return response

		def handle_response():
			if response is None:
				print_error(f'{actionStr}: read timeout')
				return False
			else:
				data = response.get_data()
				
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

		request        = generate_request()
		responseFilter = generate_required_response()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 3)
			result = handle_response()
			if result:
				break;
			print_log(f'{actionStr}: retry')
			i = i + 1
			
		return result
	
	def getParameterSize(self):
		parameterType = self.getParameterType()
		if parameterType in ParameterSize:
			return ParameterSize[parameterType]
		return 1
		
	def dataToValue(self, data):
		parameterType = self.getParameterType()
		if   parameterType == 'UINT8_T'    : return data[0]
		elif parameterType == 'UINT16_T'   : return bytesToInt(data)
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
		elif parameterType == 'UINT16_T'   : data = int(value)
		elif parameterType == 'TEMPERATURE': data = tempToData(value); signedValue = True
		elif parameterType == 'TIME_MS'    : data = timeToData(value)
		elif parameterType == 'SCHEDULE'   : data = schedulePeriodToData(value)
		elif parameterType == 'TDP_FLOAT'  : data = tdpFloatToData(value)
		
		parameterSize = self.getParameterSize()
		data_bytes = data.to_bytes(parameterSize, 'little', signed = signedValue)
		
		return list(data_bytes)

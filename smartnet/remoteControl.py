
from copy import copy

import smartnet.constants as snc
import smartnet.message as sm
import smartnet.parameter_registry as param_registry
from smartnet.crc16 import CRC16

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error


ParameterSize =  {
	'UINT8_T'    : 1,
	'UINT16_T'   : 2,
	'TEMPERATURE': 2,
	'TIME_MS'    : 4,
	'DATE'       : 5,
	'TIME'       : 4,
	'SCHEDULE'   : 4,
	'TDP_FLOAT'  : 2,
}

SCHEDULE_WEEK_DAYS = 7
SCHEDULE_PERIODS = 3
SCHEDULE_CRC_SELECTOR = (0xFF, 0xFF)


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

def date_to_data(value):
	"""Encode (day, weekday, month, year) as the packed tsDate payload."""
	if len(value) != 4:
		raise ValueError('date value must contain day, weekday, month, and year')
	day, weekday, month, year = [int(item) for item in value]
	if not 1 <= day <= 31 or not 0 <= weekday <= 6 or not 1 <= month <= 12:
		raise ValueError('date value is out of range')
	return [day, weekday, month, *year.to_bytes(2, 'little')]

def bytes_to_date(data):
	if len(data) != 5:
		raise ValueError('date data must contain five bytes')
	return (data[0], data[1], data[2], int.from_bytes(data[3:5], 'little'))

def clock_time_to_data(value):
	"""Encode (hour, minute, second, is_dst) as the packed tsTime payload."""
	if len(value) != 4:
		raise ValueError('time value must contain four components')
	hour, minute, second, is_dst = [int(item) for item in value]
	if not 0 <= hour <= 23 or not 0 <= minute <= 59 or not 0 <= second <= 59:
		raise ValueError('time value is out of range')
	return [hour, minute, second, is_dst]

def bytes_to_clock_time(data):
	if len(data) != 4:
		raise ValueError('time data must contain four bytes')
	return tuple(data)

def schedule_value_to_data(value):
	"""Encode (start_minutes, end_minutes) as two little-endian uint16 values."""
	if len(value) != 2:
		raise ValueError('schedule value must contain start and end minutes')

	start_minutes, end_minutes = [int(item) for item in value]
	if not 0 <= start_minutes < 24 * 60:
		raise ValueError('schedule start minutes are out of range')
	if not 0 <= end_minutes <= 24 * 60:
		raise ValueError('schedule end minutes are out of range')

	return [
		*start_minutes.to_bytes(2, 'little'),
		*end_minutes.to_bytes(2, 'little'),
	]

def bytesToInt(data, littleEndian = False):
	value = concatByteArray(data, littleEndian)
	return value

def bytesToTime(data, littleEndian = False):
	value = bytesToInt(data, littleEndian)
	value /=1000
	return value

def bytes_to_schedule_value(data):
	if len(data) != 4:
		raise ValueError('schedule data must contain four bytes')
	return (
		int.from_bytes(data[0:2], 'little'),
		int.from_bytes(data[2:4], 'little'),
	)


def schedule_table_to_bytes(schedule_table):
	"""Flatten the 21 values in weekday/period order for CRC calculation."""
	values = list(schedule_table)
	if len(values) != SCHEDULE_WEEK_DAYS * SCHEDULE_PERIODS:
		raise ValueError('schedule table must contain 21 values')

	data = []
	for value in values:
		data.extend(schedule_value_to_data(value))
	return data


def schedule_table_crc(schedule_table):
	return CRC16.calc(schedule_table_to_bytes(schedule_table))


def schedule_crc_to_data(value):
	return list(int(value).to_bytes(2, 'little'))


def bytes_to_schedule_crc(data):
	if len(data) != 2:
		raise ValueError('schedule CRC data must contain two bytes')
	return int.from_bytes(data, 'little')
	

class RemoteControlParameter(object):
	'''
		parameterType - value type used in CANBUS data transfer.
		Can be 
		'UINT8_T'    : 1 byte value, unsigned
		'TEMPERATURE': 2 byte value, used mostly for temperature. Value x10
		'TIME_MS'    : 4 byte value, used for time parameters. Milliseconds
		'SCHEDULE'   : table parameter (day, period). One table element - 4 bytes: 2 bytes - period start minutes, 2 bytes - end minutes.
		'TDP_FLOAT'  : two decimal places float value x100. Used mostly for heating slope
	'''
	def __init__(self,
		programType    = None,
		parameterId    = None,
		parameterValue = None,
		parameterIndex = None,
		programId      = None,
		parameterCode  = None
		):
		if parameterCode:
			self._programType, self._parameterId = parameterCode
		else:
			self._programType    = programType
			self._parameterId    = parameterId
			
		self._parameterValue = parameterValue
		self._parameterIndex = parameterIndex
		self._programId      = programId

	def setProgramId(self, programId): self._programId = programId
	
	def get_value            (self): return self._parameterValue
	def get_program_type     (self): return self._programType
	def get_parameter_id     (self): return self._parameterId
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
		
		if self.getParameterType() in ('SCHEDULE', 'DATE', 'TIME'):
			actionStr = f'prg {self._programId} write parameter {self._programType}.{self._parameterId}.{self._parameterIndex} = {self._parameterValue}'
		elif self._parameterIndex is None:
			actionStr = f'prg {self._programId} write parameter {self._programType}.{self._parameterId} = {self._parameterValue:.2f}'
		else:
			actionStr = f'prg {self._programId} write parameter {self._programType}.{self._parameterId}.{self._parameterIndex} = {self._parameterValue:.2f}'

#		print(actionStr)
		
		def generate_request():
			parameterId = self.get_parameter_id()
			
			parameterValue = self.valueToData(self._parameterValue)
			
			if self.getParameterType() == 'SCHEDULE':
				data = [self._programType, parameterId, *self._parameterIndex]
			elif self._parameterIndex is None:
				data = [self._programType, parameterId]
			else:
				data = [self._programType, parameterId, self._parameterIndex]
			
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
		
		parameter_size = self.getParameterSize()
		data_size = parameter_size + self.getParameterIndexSize()
		
		# response flag don't fit in message body so no need to wait confirm
		# actually instead we should wait for response with new data value but I'm lazy to do it
		if data_size >= 6:
			confirm = False
			
		if confirm == False:
			request.send()
			return True
		
		responseFilter = generate_required_response()

		i = 0
		had_retry = False
		while i < 3:
			response = request.send(responseFilter, 3)
			result = handle_response()
			if result:
				if had_retry:
					print_log(f'{actionStr}: write succeeded after retry')
				break;
			print_log(f'{actionStr}: retry')
			had_retry = True
			i = i + 1
			
		return result
	
	def read(self):
		if self._programId is None:
			print_error('wrong programId')
			return False
		
		if self.getParameterType() == 'SCHEDULE':
			if not self._is_schedule_selector_valid():
				return False
			actionStr = f'prg {self._programId} read parameter {self._programType}.{self._parameterId}.{self._parameterIndex}'
		elif self._parameterIndex is None:
			actionStr = f'prg {self._programId} read parameter {self._programType}.{self._parameterId}'
		else:
			actionStr = f'prg {self._programId} read parameter {self._programType}.{self._parameterId}.{self._parameterIndex}'

		def generate_request():
			parameterId = self.get_parameter_id()
			
			if self.getParameterType() == 'SCHEDULE':
				data = [self._programType, parameterId, *self._parameterIndex]
			elif self._parameterIndex is None:
				data = [self._programType, parameterId]
			else:
				data = [self._programType, parameterId, self._parameterIndex]

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
				
				if self.getParameterType() == 'SCHEDULE':
					valuePos = 4
				elif self._parameterIndex is None:
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
		if parameterType == 'SCHEDULE' and self._parameterIndex == SCHEDULE_CRC_SELECTOR:
			return 2
		if parameterType in ParameterSize:
			return ParameterSize[parameterType]
		return 1

	def getParameterIndexSize(self):
		if self._parameterIndex is None:
			return 0
		if self.getParameterType() == 'SCHEDULE':
			return 2
		return 1
		
	def dataToValue(self, data):
		parameterType = self.getParameterType()
		if   parameterType == 'UINT8_T'    : return data[0]
		elif parameterType == 'UINT16_T'   : return bytesToInt(data)
		elif parameterType == 'TEMPERATURE': return bytesToTemp(data)
		elif parameterType == 'TIME_MS'    : return bytesToTime(data)
		elif parameterType == 'DATE'       : return bytes_to_date(data)
		elif parameterType == 'TIME'       : return bytes_to_clock_time(data)
		elif parameterType == 'SCHEDULE':
			if self._parameterIndex == SCHEDULE_CRC_SELECTOR:
				return bytes_to_schedule_crc(data)
			return bytes_to_schedule_value(data)
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
		elif parameterType == 'DATE'       : return date_to_data(value)
		elif parameterType == 'TIME'       : return clock_time_to_data(value)
		elif parameterType == 'SCHEDULE':
			if self._parameterIndex == SCHEDULE_CRC_SELECTOR:
				return schedule_crc_to_data(value)
			return schedule_value_to_data(value)
		elif parameterType == 'TDP_FLOAT'  : data = tdpFloatToData(value)
		
		parameterSize = self.getParameterSize()
		data_bytes = data.to_bytes(parameterSize, 'little', signed = signedValue)
		
		return list(data_bytes)

	def _is_schedule_selector_valid(self):
		if not isinstance(self._parameterIndex, (tuple, list)) or len(self._parameterIndex) != 2:
			print_error('schedule parameterIndex must be (week_day, period)')
			return False

		week_day, period = self._parameterIndex
		if (week_day, period) == SCHEDULE_CRC_SELECTOR:
			return True
		if not 0 <= week_day < SCHEDULE_WEEK_DAYS or not 0 <= period < SCHEDULE_PERIODS:
			print_error('schedule selector is out of range')
			return False
		return True

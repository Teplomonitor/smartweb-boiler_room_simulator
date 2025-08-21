
from smartnet.remoteControl import RemoteControlParameter as RemoteControlParameter

class HeatingCircuitSettings(object):
	def __init__(self,
			source         = None,
			heatingSlope   = None,
			):
		self._source         = source
		self._heatingSlope   = heatingSlope

	def get(self):
		return [
			RemoteControlParameter('CONSUMER', 'GENERATOR_ID', self._source),
			RemoteControlParameter('CIRCUIT', 'HEATING_SLOPE', self._heatingSlope, parameterType = 'TDP_FLOAT'),
		]
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

class DhwSettings(object):
	def __init__(self,
			source         = None,
			):
		self._source         = source

	def get(self):
		return [
			RemoteControlParameter('CONSUMER', 'GENERATOR_ID', self._source),
		]
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

class SnowMelterSettings(object):
	def __init__(self,
			source         = None,
			alarmProgram   = None
			):
		self._source         = source
		self._alarmProgram   = alarmProgram

	def get(self):
		return [
			RemoteControlParameter('CONSUMER', 'GENERATOR_ID'    , self._source),
			RemoteControlParameter('CONSUMER', 'ALARM_PROGRAM_ID', self._alarmProgram),
		]
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

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
					RemoteControlParameter('CASCADE_MANAGER', 'PARAM_TEMPERATURE_SOURCE_ID', source, i)
				)
			i = i + 1

		return result

	def getSourceList(self):
		return self._sourceList


class RoomSettings(object):
	def __init__(self,
			source_1 = None,
			source_2 = None,
			source_3 = None,
			):

		self._sourceList = [
			source_1,
			source_2,
			source_3,
			]

	def get(self):
		return [
				RemoteControlParameter('ROOM_DEVICE', 'RESPONSIBLE_CIRCUIT_1', self._sourceList[0]),
				RemoteControlParameter('ROOM_DEVICE', 'RESPONSIBLE_CIRCUIT_2', self._sourceList[1]),
				RemoteControlParameter('ROOM_DEVICE', 'RESPONSIBLE_CIRCUIT_3', self._sourceList[2]),
			]
		
	def getSourceList(self):
		return self._sourceList
	

class DistrictHeatingSettings(object):
	def __init__(self,
			source         = None,
			):
		self._source         = source

	def get(self):
		return [
			RemoteControlParameter('DISTRICT_HEATING', 'PARAM_TEMPERATURE_SOURCE_ID', self._source),
		]
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

class SwimmingPoolSettings(object):
	def __init__(self,
			source         = None,
			):
		self._source         = source

	def get(self):
		return [
			RemoteControlParameter('CONSUMER', 'GENERATOR_ID', self._source),
		]
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

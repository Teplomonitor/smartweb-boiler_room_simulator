
import smartnet.constants as snc
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
			RemoteControlParameter(
				snc.ProgramType['CONSUMER'], 
				snc.ConsumerParameter['GENERATOR_ID'], 
				self._source),
			RemoteControlParameter(
				snc.ProgramType['CIRCUIT'], 
				snc.CircuitParameter['HEATING_SLOPE'], 
				self._heatingSlope),
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
			RemoteControlParameter(
				snc.ProgramType['CONSUMER'], 
				snc.ConsumerParameter['GENERATOR_ID'], 
				self._source),
		]
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

class SnowMelterSettings(object):
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
					RemoteControlParameter(
						snc.ProgramType['CASCADE_MANAGER'], 
						snc.CascadeManagerParameter['PARAM_TEMPERATURE_SOURCE_ID'], 
						source, i)
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
		result = []
		i = 0
		for source in self._sourceList:
			if source:
				result.append(
					RemoteControlParameter(
						snc.ProgramType['ROOM_DEVICE'], 
						snc.RoomDeviceParameter['RESPONSIBLE_CIRCUIT_1'] + i, 
						source)
				)
			i = i + 1

		return result
		
	def getSourceList(self):
		return self._sourceList
	

class DistrictHeatingSettings(object):
	def __init__(self,
			source         = None,
			):
		self._source         = source

	def get(self):
		return [
			RemoteControlParameter(
				snc.ProgramType['DISTRICT_HEATING'], 
				snc.DistrictHeatingParameter['PARAM_TEMPERATURE_SOURCE_ID'], 
				self._source),
		]
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

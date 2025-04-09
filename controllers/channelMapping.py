

class Channel(object):
	'''
	classdocs
	'''

	def __init__(self, mapping = None, value = None):
		'''
		Constructor
		'''
		self._mapping = mapping
		self._value   = value

	def getMapping(self): return self._mapping
	def getValue  (self): return self._value

	def setMapping(self, mapping): self._mapping = mapping
	def setValue  (self, value  ): self._value   = value


class ChannelMapping(object):
	'''
	classdocs
	'''
	Type = {
		'CHANNEL_SENSOR_LOCAL' : 0,
		'CHANNEL_RELAY_LOCAL'  : 1,
		'CHANNEL_SENSOR'       : 2,
		'CHANNEL_RELAY'        : 3,
		'CHANNEL_INPUT'        : 4,
		'CHANNEL_OUTPUT'       : 5,
		'CHANNEL_RESERVED'     : 6,
		'CHANNEL_UNDEFINED'    : 7,
	};

	def __init__(self, channelId, channelType, hostId):
		self._channelId   = channelId
		self._channelType = channelType
		self._hostId      = hostId

	def getChannelId   (self): return self._channelId  
	def getChannelType (self): return self._channelType
	def getHostId      (self): return self._hostId

	def getRaw(self, part=None):
		raw = (
			(          self._hostId       <<  0) |
			(          self._channelId    <<  8) |
			(self.Type[self._channelType] << 13))
		
		if part is None:
			return raw

		if part == 0: return (raw >> 0) &0xFF
		if part == 1: return (raw >> 8) &0xFF



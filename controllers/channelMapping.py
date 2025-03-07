

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
	def getRaw(self):
		raw = (
			(self._hostId      <<  0) |
			(self._channelId   <<  8) |
			(self._channelType << 13))
		return raw


from functions.programLog import ParameterLog as ChannelLog

from gui.parameter import GuiParameter as GuiParameter

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
	
	def isMapped(self):
		if self._channelType == 'CHANNEL_UNDEFINED':
			return False
		return True

	def getRaw(self, part=None):
		raw = (
			(          self._hostId       <<  0) |
			(          self._channelId    <<  8) |
			(self.Type[self._channelType] << 13))
		
		if part is None:
			return raw

		if part == 0: return (raw >> 0) &0xFF
		if part == 1: return (raw >> 8) &0xFF



class Channel(GuiParameter):
	'''
	classdocs
	'''

	def __init__(self, mapping = None, value = None, title = None, gui = None):
		'''
		Constructor
		'''
		super().__init__(value, title, gui)
		
		self._mapping = mapping
		self._log     = ChannelLog('SENSOR', title)

	def getMapping(self): return self._mapping
	def isMapped(self):
		if self._mapping:
			return self._mapping.isMapped()
		
	def setMapping(self, mapping): self._mapping = mapping
	
	def setValue  (self, value):
		super().setValue(value)
		self._log.append(value)
		
	def setTitle  (self, title  ):
		super().setTitle(title)
		self._log.setTitle(title)
		
	def setLogType(self, logType): self._log.setSaveType(logType)
	
	def saveLog(self, title):
		self._log.saveToCsv(title)

class InputChannel(Channel):
	'''
	classdocs
	'''

	def __init__(self, mapping = None, value = None, title = None, gui = None):
		'''
		Constructor
		'''
		super().__init__(mapping, value, title, gui)
		
		self.setLogType('TEMPERATURE')
		
	def setValue  (self, value, manual = False  ):
		if self.isManual():
			if not manual:
				return
			
		super().setValue(value)
			
	def isAuto(self):
		if self._gui:
			return self._gui._autoRb.GetValue()
		return True
	
	def isManual(self):
		if self._gui:
			return self._gui._manualRb.GetValue()
		return False
	
	def onShort(self, event):
		event.Skip()
		state = self._gui._shortCheckbox.GetValue()
		if state:
			self._gui._openCheckbox.SetValue(False)
			
		self._gui._slider.Enable ( not state )
		self._gui._spinner.Enable( not state )
	
	def onOpen(self, event):
		event.Skip()
		state = self._gui._openCheckbox.GetValue()
		if state:
			self._gui._shortCheckbox.SetValue(False)
		self._gui._slider.Enable ( not state )
		self._gui._spinner.Enable( not state )
	
	
	def isShort(self):
		if self._gui:
			return self._gui._shortCheckbox.GetValue()
		return False
	
	def isOpen(self):
		if self._gui:
			return self._gui._openCheckbox.GetValue()
		return False
		
	
class OutputChannel(Channel):
	'''
	classdocs
	'''

	def __init__(self, mapping = None, value = None, title = None, gui = None):
		'''
		Constructor
		'''
		super().__init__(mapping, value, title, gui)
		
	def initGui(self):
		pass
		

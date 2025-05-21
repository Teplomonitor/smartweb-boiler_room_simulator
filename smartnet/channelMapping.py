

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


class Channel(object):
	'''
	classdocs
	'''

	def __init__(self, mapping = None, value = None, title = None, gui = None):
		'''
		Constructor
		'''
		self._mapping = mapping
		self._value   = value
		self._title   = title
		self._gui     = gui

	def getMapping(self): return self._mapping
	def isMapped(self):
		if self._mapping:
			return self._mapping.isMapped()
		
	def getValue  (self): return self._value
	def getTitle  (self): return self._title

	def setMapping(self, mapping): self._mapping = mapping
	
	def setValue  (self, value):
		self._value = value
		if self._gui:
			self._gui.SetValue(value)
		
	def setTitle  (self, title  ): self._title = title
	
	def setGui(self, gui):
		self._gui = gui
		

class InputChannel(Channel):	
	'''
	classdocs
	'''

	def __init__(self, mapping = None, value = None, title = None, gui = None):
		'''
		Constructor
		'''
		super().__init__(mapping, value, title, gui)
		
		self._min     =   0
		self._max     = 100
		
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
	
	def onSpin(self, event):
		event.Skip()
		self.setValue(self._gui._spinner.GetValue(), True)
		
	def onSpinText(self, event):
		event.Skip()
		self.setValue(int(self._gui._spinner.GetTextValue()), True)
		
	def onScroll(self, event):
		event.Skip()
		self.setValue(self._gui._slider .GetValue(), True)
	
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
	
	def setGui(self, gui):
		self._gui = gui
		
		self.initGui()

	def initGui(self):
		if self._gui:
			self._gui.SetMin(self._min)
			self._gui.SetMax(self._max)
		
	def getMin(self): return self._min
	def getMax(self): return self._max
	
	def setMin(self, value):
		self._min = value
		
		if self._gui:
			self._gui.SetMin(value)
		
	def setMax(self, value):
		self._max = value
		
		if self._gui:
			self._gui.SetMax(value)
			
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


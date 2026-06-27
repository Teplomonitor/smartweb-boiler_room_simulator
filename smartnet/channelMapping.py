
import time

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

	def get_channel_id   (self): return self._channelId  
	def get_channel_type (self): return self._channelType
	def get_host_id      (self): return self._hostId
	
	def is_mapped(self):
		if self._channelType == 'CHANNEL_UNDEFINED':
			return False
		return True

	def get_raw(self, part=None):
		raw = (
			(          self._hostId       <<  0) |
			(          self._channelId    <<  8) |
			(self.Type[self._channelType] << 13))
		
		if part is None:
			return raw

		if part == 0: return (raw >> 0) &0xFF
		if part == 1: return (raw >> 8) &0xFF

		return raw


class Channel(GuiParameter):
	'''
	classdocs
	'''

	def __init__(self
				, mapping = None
				, value = None
				, title = None
				, gui = None
				, channelId = 0
				):
		'''
		Constructor
		'''
		super().__init__(value, title, gui = gui)
		
		self._id      = channelId
		self._mapping = mapping
		self._log     = ChannelLog('SENSOR', title)

	def get_id     (self): return self._id
	def get_mapping(self): return self._mapping
	
	def is_mapped(self):
		if self._mapping:
			return self._mapping.is_mapped()
		return False
		
	def set_mapping(self, mapping): self._mapping = mapping
	
	def set_value  (self, value, manual = False):
		super().set_value(value, manual)
		self._log.append(value)
		
	def set_title  (self, title  ):
		super().set_title(title)
		self._log.set_title(title)
		
	def setLogType(self, logType): self._log.setSaveType(logType)
	
	def save_log(self, title):
		self._log.saveToCsv(title)

class InputChannel(Channel):
	'''
	classdocs
	'''

	def __init__(self
				, mapping = None
				, value   = None
				, title   = None
				, gui     = None
				, channelId =   0
				, minValue  =   0
				, maxValue  = 100
				, units     = '°C'
				):
		'''
		Constructor
		'''
		super().__init__(mapping, value, title, gui, channelId)
		
		self.setLogType('TEMPERATURE')
		
		self._isManual = False
		self._state    = 'normal'
		self.setMin(minValue)
		self.setMax(maxValue)
		self.setUnits(units)
		
	def set_value  (self, value, manual = False  ):
		if self.isManual():
			if not manual:
				return
		
		if   value == 'short': self.setShort (True); return
		elif value == 'open' : self.setOpen  (True); return
		else                 : self.setNormal()
		
		super().set_value(value, manual)
		
	def isAuto(self):
		return not self._isManual
	
	def isManual(self):
		return self._isManual
	
	def set_manual(self, value):
		self._isManual = value
		if self._gui:
			self._gui._manualRb.SetValue(    value)
			self._gui._autoRb  .SetValue(not value)
	
	def onManual(self, event):
		event.Skip()
		self.set_manual(True)
		
	def onAuto(self, event):
		event.Skip()
		self.set_manual(False)
		
	
	def onShort(self, event = None):
		if event:
			event.Skip()
		state = self._gui._shortCheckbox.GetValue()
		
		self.setShort(state)
	
	def onOpen(self, event = None):
		event.Skip()
		state = self._gui._openCheckbox.GetValue()
		
		self.setOpen(state)
	
	def isShort(self): return self._state == 'short'
	def isOpen (self): return self._state == 'open'
		
	def setShort(self, state):
		if state:
			self._state = 'short'
		else:
			self._state = 'normal'
			
		if self._gui:
			self._gui._shortCheckbox.SetValue(state)
			self._gui._slider.Enable ( not state )
			self._gui._spinner.Enable( not state )
			if state:
				self._gui._openCheckbox.SetValue(False)
		
	def setOpen(self, state):
		if state:
			self._state = 'open'
		else:
			self._state = 'normal'
			
		if self._gui:
			self._gui._openCheckbox.SetValue(state)
			self._gui._slider.Enable ( not state )
			self._gui._spinner.Enable( not state )
			if state:
				self._gui._shortCheckbox.SetValue(False)
				
	def setNormal(self):
		if self._state == 'normal':
			return
		
		self._state = 'normal'
		if self._gui:
			self._gui._openCheckbox .SetValue(False)
			self._gui._shortCheckbox.SetValue(False)
			self._gui._slider .Enable( True )
			self._gui._spinner.Enable( True )
	
	def enable_gui_control(self):
		if self._gui:
			self._gui._openCheckbox .Enable( True )
			self._gui._shortCheckbox.Enable( True )
			self._gui._manualRb.Enable( True )
			self._gui._autoRb  .Enable( True )
			if self._state == 'normal':
				self._gui._slider .Enable( True )
				self._gui._spinner.Enable( True )
		
	def disable_gui_control(self):
		if self._gui:
			self._gui._openCheckbox .Enable( False )
			self._gui._shortCheckbox.Enable( False )
			self._gui._slider .Enable( False )
			self._gui._spinner.Enable( False )
			self._gui._manualRb.Enable( False )
			self._gui._autoRb  .Enable( False )
		
class OutputChannel(Channel):
	'''
	classdocs
	'''

	def __init__(self
				, mapping = None
				, value = None
				, title = None
				, gui = None
				, channelId = 0
				):
		'''
		Constructor
		'''
		super().__init__(mapping, value, title, gui, channelId)
		self._log.setType('RELAY')
		self._lastUpdateTime = None
		
	def set_value(self, value, manual = False):
#		print(f'{self.get_title()} = {value}')
		super().set_value(value, manual)
		self._lastUpdateTime = time.time()
		
	def valueIsUpToDate(self):
		if self._lastUpdateTime is None:
			return False
		now = time.time()
		return now -self._lastUpdateTime < 10
	
	def init_gui(self):
		self.setGuiValue(self._value)
		

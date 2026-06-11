'''
@author: admin
'''
try:
	import wx
	
except ImportError:
	print('import gui fail. Please install wxPython if you wish to use gui: pip install -U wxPython')

class GuiParameter(object):
	'''
	classdocs
	'''

	def __init__(
			self
			, value = None
			, title = None
			, minValue = 0
			, maxValue = 100
			, step = 0.1
			, units = '°C'
			, gui = None
			):
		'''
		Constructor
		'''
		self._value   = value
		self._title   = title
		self._gui     = gui
		self._min     = minValue
		self._max     = maxValue
		self._step    = step
		self._units   = units
		self._needUpdateGuiValue = True
		self._options = None
		
		if self._value is None:
			self._value = self._min
		
	def getValue  (self):
		if self._needUpdateGuiValue:
			self.setGuiValue(self._value)
			
		return self._value
	def getTitle  (self): return self._title
	def getUnits  (self): return self._units
	def getOptions(self): return self._options
	
	def setValue  (self, value, manual = False):
		self._value = value
		self.setGuiValue(value)
		
	def setTitle  (self, title)  : self._title   = title
	def setUnits  (self, units)  : self._units   = units
	def setOptions(self, options):
		self._options = options
		if self._gui:
			self._gui.setOptions(options)
		
	
	def getSelectedOption(self):
		if self._gui:
			return self._gui.getSelectedOption()
		
	def onSpin(self, event):
		event.Skip()
		self.setValue(self._gui._spinner.GetValue(), True)
		
	def onSpinText(self, event):
		event.Skip()
		self.setValue(int(float(self._gui._spinner.GetTextValue())), True)
		
	def onScroll(self, event):
		event.Skip()
		self.setValue(self._gui._slider .GetValue(), True)
	
	def setGuiValue(self, value):
		if self._gui:
			self._gui.SetValue(value)
			self._needUpdateGuiValue = False
		
	def setGui(self, gui):
		self._gui = gui
		self.initGui()

	def initGui(self):
		if self._gui:
			self._gui.SetMin  (self._min)
			self._gui.SetMax  (self._max)
			self._gui.SetIncrement(self._step)
			self.setGuiValue  (self._value)
		
	def getMin (self): return self._min
	def getMax (self): return self._max
	def getStep(self): return self._step
	
	def setMin(self, value):
		self._min = value
		
		if self._gui:
			self._gui.SetMin(value)
		
	def setMax(self, value):
		self._max = value
		
		if self._gui:
			self._gui.SetMax(value)
			
	def setStep(self, value):
		self._step = value
		
		if self._gui:
			self._gui.SetIncrement(value)
			
	def setProperties(self, minValue, maxValue, step, units):
		self.setMin(minValue)
		self.setMax(maxValue)
		self.setStep(step)
		self.setUnits(units)
			

class GuiParameterApi(object):
	def __init__(self, spinner, slider, combobox = None):
		self._spinner       = spinner
		self._slider        = slider
		self._combobox      = combobox
	
	def SetValue(self, value):
		wx.CallAfter(self.SetValueNow, value)
		
	def SetValueNow(self, value):
		self._spinner.SetValue(value)
		self._slider .SetValue(int(value + 0.5))
		
	def SetMin(self, value):
		self._spinner.SetMin(value)
		self._slider .SetMin(int(value))
		
	def SetMax(self, value):
		self._spinner.SetMax(value)
		self._slider .SetMax(int(value))
		
	def SetIncrement(self, value):
		self._spinner.SetIncrement(value)
		
	def getSelectedOption(self):
		if self._combobox:
			return self._combobox.GetStringSelection()
	
	def setOptions(self, options):
		if self._combobox:
			return self._combobox.Append(options)

class GuiInputChannel(GuiParameterApi):
	def __init__(self, spinner, slider, shortCheckbox, openCheckbox, autoRb, manualRb):
		super().__init__(spinner, slider)
		self._shortCheckbox = shortCheckbox
		self._openCheckbox  = openCheckbox 
		self._autoRb        = autoRb       
		self._manualRb      = manualRb    

class GuiOutputChannel(object):
	def __init__(self, gauge):
		self._gauge       = gauge
		
	def SetValue(self, value):
		wx.CallAfter(self.SetValueNow, value)
		
	def SetValueNow(self, value):
		self._gauge.SetValue(value)
		

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

	def __init__(self, value = None, title = None, gui = None):
		'''
		Constructor
		'''
		self._value   = value
		self._title   = title
		self._gui     = gui
		self._min     =   0
		self._max     = 100
		self._step    = 0.1
		self._units   = '°C'
		self._needUpdateGuiValue = True
		
		if self._value is None:
			self._value = self._min
		
	def getValue  (self):
		if self._needUpdateGuiValue:
			self.setGuiValue(self._value)
			
		return self._value
	def getTitle  (self): return self._title
	def getUnits  (self): return self._units
	
	def setValue  (self, value, manual = False):
		self._value = value
		self.setGuiValue(value)
		
		
	def setTitle(self, title): self._title = title
	def setUnits(self, units): self._units = units
	
	def onSpin(self, event):
		event.Skip()
		self.setValue(self._gui._spinner.GetValue(), True)
		
	def onSpinText(self, event):
		event.Skip()
		self.setValue(int(self._gui._spinner.GetTextValue()), True)
		
	def onScroll(self, event):
		event.Skip()
		self.setValue(self._gui._slider .GetValue(), True)
	
	def setGuiValue(self, value):
		if self._gui:
			self._gui.SetValue(value)
		
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
	def __init__(self, spinner, slider):
		self._spinner       = spinner
		self._slider        = slider
	
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

class GuiInputChannel(GuiParameterApi):
	def __init__(self, spinner, slider, shortCheckbox, openCheckbox, autoRb, manualRb):
		super().__init__(spinner, slider)
		self._shortCheckbox = shortCheckbox
		self._openCheckbox  = openCheckbox 
		self._autoRb        = autoRb       
		self._manualRb      = manualRb    

class GuiOutputChannel():
	def __init__(self, gauge):
		self._gauge       = gauge
		
	def SetValue(self, value):
		wx.CallAfter(self.SetValueNow, value)
		
	def SetValueNow(self, value):
		self._gauge.SetValue(value)
		

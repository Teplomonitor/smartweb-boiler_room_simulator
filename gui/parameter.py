'''
@author: admin
'''

class Gui(object):
	def __init__(self, spinner, slider):
		self._spinner       = spinner
		self._slider        = slider
	
	def SetValue(self, value):
		self._spinner.SetValue(value)
		self._slider .SetValue(int(value + 0.5))
		
	def SetMin(self, value):
		self._spinner.SetMin(value)
		self._slider .SetMin(int(value))
		
	def SetMax(self, value):
		self._spinner.SetMax(value)
		self._slider .SetMax(int(value))


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
		
	def getValue  (self): return self._value
	def getTitle  (self): return self._title
	
	def setValue  (self, value):
		self._value = value
		if self._gui:
			self._gui.SetValue(value)
		
		
	def setTitle  (self, title  ):
		self._title = title
		
	
	def onSpin(self, event):
		event.Skip()
		self.setValue(self._gui._spinner.GetValue(), True)
		
	def onSpinText(self, event):
		event.Skip()
		self.setValue(int(self._gui._spinner.GetTextValue()), True)
		
	def onScroll(self, event):
		event.Skip()
		self.setValue(self._gui._slider .GetValue(), True)
		
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
			
'''

@author: admin
'''


class Channel():
	def __init__(self, spinner, slider, shortCheckbox, openCheckbox, autoRb, manualRb):
		self._spinner       = spinner      
		self._slider        = slider       
		self._shortCheckbox = shortCheckbox
		self._openCheckbox  = openCheckbox 
		self._autoRb        = autoRb       
		self._manualRb      = manualRb    
	
	def SetValue(self, value):
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
		

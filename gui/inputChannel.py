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
		
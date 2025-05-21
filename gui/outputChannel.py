'''
@author: admin
'''

class Channel():
	def __init__(self, gauge):
		self._gauge       = gauge  
	
	def SetValue(self, value):
		self._gauge.SetValue(value)
		

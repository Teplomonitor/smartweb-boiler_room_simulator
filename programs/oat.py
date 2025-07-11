'''
@author: admin
'''

from .program import Program

class Oat(Program):
	'''
	classdocs
	'''


	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		inputsRange = [
			[-40, 40],
		]
		
		self.setInputsRange(inputsRange)
		
		self._inputId = {
			'outdoorTemperature'  : 0,
		}
		
	def getOutdoorTemperature(self):
		return self.getInputChannel(self._inputId['outdoorTemperature'])
	
	def getGuiColor (self): return 'blue'

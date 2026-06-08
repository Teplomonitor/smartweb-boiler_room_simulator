'''
@author: admin
'''

from .program import Program

class Oat(Program):
	'''
	classdocs
	'''

	def getType(self): return 'OUTDOOR_SENSOR'
	
	def getInputTitles(self):
		return [
			'Улица',
			]

	def getOutputTitles(self):
		return [
			]


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

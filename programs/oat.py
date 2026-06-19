'''
@author: admin
'''

from .program import InputInfo
from .program import Program

class Oat(Program):
	'''
	classdocs
	'''

	@staticmethod
	def getType(): return 'OUTDOOR_SENSOR'
	
	def initInputs(self):
		self._inputs['outdoorTemperature'] = InputInfo(0, 'Улица', -40, 40)
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	def getOutdoorTemperature(self): return self.getInputChannel('outdoorTemperature')
	
	def getGuiColor (self): return 'blue'

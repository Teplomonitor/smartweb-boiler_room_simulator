'''
@author: admin
'''

from .program import input_info
from .program import Program

class Oat(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return 'OUTDOOR_SENSOR'
	
	def init_inputs(self):
		self._inputs['outdoorTemperature'] = input_info(0, 'Улица', -40, 40)
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	def getOutdoorTemperature(self): return self.get_input_channel('outdoorTemperature')
	
	def get_gui_color (self): return 'blue'

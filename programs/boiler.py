'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class Boiler(Program):
	'''
	classdocs
	'''


	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		rate = GuiParameter(3000, 'Расход')
		rate.setProperties(0, 5000, 1, 'кг/ч')
		
		self._parameters['max_flow_rate'] = rate
		
	def getMaxFlowRate(self):
		return self._parameters['max_flow_rate'].getValue()
	
	def getGuiColor (self): return 'red'

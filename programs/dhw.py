'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class Dhw(Program):
	'''
	classdocs
	'''


	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
				
		rate = GuiParameter(1000, 'Расход')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		
		self._parameters['max_flow_rate'] = rate
	
	def getMaxFlowRate(self):
		return self._parameters['max_flow_rate'].getValue()

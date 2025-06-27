'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class HeatingCircuit(Program):
	'''
	classdocs
	'''


	def __init__(self, preset):
		'''
		Constructor
		'''
		super().__init__(preset)
		
		rate = GuiParameter(1000, 'Расход')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		
		self._parameters['max_flow_rate'] = rate
	
	def getMaxFlowRate(self):
		return self._parameters['max_flow_rate'].getValue()

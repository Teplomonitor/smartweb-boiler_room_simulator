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
		
		self._parameters['max_flow_rate'] = GuiParameter(1000, 'Расход')
		self._parameters['max_flow_rate'].setMin(0)
		self._parameters['max_flow_rate'].setMax(3000)
		self._parameters['max_flow_rate'].setStep(1)
		
		self._parameters['max_flow_rate'].setUnits('кг/ч')
	
	def getMaxFlowRate(self):
		return self._parameters['max_flow_rate'].getValue()

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
		
		self._parameters['max_flow_rate'] = GuiParameter(1000, 'Проток')
		self._parameters['max_flow_rate'].setMin(0)
		self._parameters['max_flow_rate'].setMax(10000)


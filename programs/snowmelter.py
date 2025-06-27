'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class Snowmelter(Program):
	'''
	classdocs
	'''

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		inputsRange = [
			[-10, 100],
			[-10,  100],
			[-30,   40],
		]
		
		self.setInputsRange(inputsRange)
		
		rate = GuiParameter(1000, 'Расход до теплообменника')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		self._parameters['max_flow_rate1'] = rate
		
		rate = GuiParameter(1000, 'Расход после теплообменника')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		self._parameters['max_flow_rate2'] = rate
	
	def getMaxFlowRate1(self):
		return self._parameters['max_flow_rate1'].getValue()
	
	def getMaxFlowRate2(self):
		return self._parameters['max_flow_rate2'].getValue()

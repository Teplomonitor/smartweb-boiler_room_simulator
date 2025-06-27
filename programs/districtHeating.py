'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class DistrictHeating(Program):
	'''
	classdocs
	'''

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		rate = GuiParameter(3000, 'Расход в доме')
		rate.setProperties(100, 6000, 1, 'кг/ч')
		self._parameters['max_flow_rate1'] = rate
		
		rate = GuiParameter(3000, 'Расход в городе')
		rate.setProperties(100, 6000, 1, 'кг/ч')
		self._parameters['max_flow_rate2'] = rate
	
	def getMaxFlowRate1(self):
		return self._parameters['max_flow_rate1'].getValue()
	
	def getMaxFlowRate2(self):
		return self._parameters['max_flow_rate2'].getValue()

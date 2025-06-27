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
		
		power = GuiParameter(1, 'Мощность')
		power.setProperties(0, 10, 1, 'кВт')
		
		self._parameters['max_flow_rate'] = rate
		self._parameters['max_power']= power
	
	def getMaxFlowRate(self):
		return self._parameters['max_flow_rate'].getValue()

	def getMaxPower(self):
		return self._parameters['max_power'].getValue()
	
	def getGuiColor (self): return 'orange'

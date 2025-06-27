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
		
		power = GuiParameter(30, 'Мощность')
		power.setProperties(5, 300, 1, 'кВт')
		
		self._parameters['max_flow_rate'] = rate
		self._parameters['max_power']= power
		
	def getMaxFlowRate(self):
		return self._parameters['max_flow_rate'].getValue()
	
	def getMaxPower(self):
		return self._parameters['max_power'].getValue()
	
	def getGuiColor (self): return 'yellow'

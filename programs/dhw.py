'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class Dhw(Program):
	'''
	classdocs
	'''

	def getType(self): return 'DHW'
	
	def getInputTitles(self):
		return [
			'Т бойлера',
			'Проток',
			'Т обратки',
			]

	def getOutputTitles(self):
		return [
			'Насос загрузки',
			'Цирк. насос',
			'А. насос загрузки',
			'Смес. откр',
			'Смес. закр',
			]

	def initGuiParameters(self):
		rate = GuiParameter(1000, 'Расход')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		self._parameters['max_flow_rate'] = rate
		
		power = GuiParameter(1, 'Мощность')
		power.setProperties(0, 10, 1, 'кВт')
		self._parameters['max_power']= power
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
				
	def getGuiColor (self): return 'orange'

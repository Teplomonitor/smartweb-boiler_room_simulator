'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class HeatingCircuit(Program):
	'''
	classdocs
	'''
	def getType(self): return 'HEATING_CIRCUIT'
	
	def getInputTitles(self):
		return [
			'Т подачи',
			'Термостат',
			'Внешний запрос',
			'Управление насосом',
			'Т обратки',
			]

	def getOutputTitles(self):
		return [
			'А.смеситель',
			'Смес. откр',
			'Смес. закр',
			'Насос',
			'Клапан',
			'Насос ТО',
			'А. насос',
			]

	def initGuiParameters(self):
		rate = GuiParameter(1000, 'Расход')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		self._parameters['max_flow_rate'] = rate
		
		power = GuiParameter(3, 'Мощность')
		power.setProperties(0, 10, 1, 'кВт')
		self._parameters['max_power']= power
		
	def __init__(self, preset):
		'''
		Constructor
		'''
		super().__init__(preset)
		
	def getGuiColor (self): return 'green'


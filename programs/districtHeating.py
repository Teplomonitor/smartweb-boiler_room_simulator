'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class DistrictHeating(Program):
	'''
	classdocs
	'''

	def getType(self): return 'DISTRICT_HEATING'
	
	def getInputTitles(self):
		return [
			'Подача из города',
			'Обратка в город',
			'Подача в дом',
			'Обратка из дома',
			'Теплосчётчик',
			'Расход',
			'Внешний запрос',
			]

	def getOutputTitles(self):
		return [
			'Насос загрузки',
			'Цирк. насос',
			'Клапан',
			'А. клапан',
			]

	def initGuiParameters(self):
		self._parameters['max_flow_rate1'] = GuiParameter(3000, 'Расход в доме', 100, 6000, 1, 'кг/ч')
		self._parameters['max_flow_rate2'] = GuiParameter(3000, 'Расход в городе', 100, 6000, 1, 'кг/ч')
		self._parameters['max_power'     ] = GuiParameter(30, 'Мощность', 5, 300, 1, 'кВт')
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	
	def getMaxFlowRate1(self):
		return self._parameters['max_flow_rate1'].getValue()
	
	def getMaxFlowRate2(self):
		return self._parameters['max_flow_rate2'].getValue()

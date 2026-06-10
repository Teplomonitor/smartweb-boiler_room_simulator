'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class Boiler(Program):
	'''
	classdocs
	'''

	def getType(self): return 'BOILER'
	
	def getInputTitles(self):
		return [
			'Т котла',
			'Т обратки',
			'Внешний запрос',
			'Ошибка котла',
			]

	def getOutputTitles(self):
		return [
			'Насос',
			'Ступень 1',
			'Ступень 2',
			'Мощность',
			'Температура',
			'Контроль обратки',
			]

	_inputId = {
		'temperature'         : 0,
		'backwardTemperature' : 1,
		'outsideRequest'      : 2,
		'error'               : 3,
	}

	_outputId = {
		'pump'                : 0,
		'burner1'             : 1,
		'burner2'             : 2,
		'power'               : 3,
		'temperature'         : 4,
		'backwardTemperature' : 5,
	}
		
	def initGuiParameters(self):
		rate = GuiParameter(3000, 'Расход')
		rate.setProperties(0, 5000, 1, 'кг/ч')
		self._parameters['max_flow_rate'] = rate
		
		power = GuiParameter(30, 'Мощность')
		power.setProperties(5, 300, 1, 'кВт')
		self._parameters['max_power']= power
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		
	def getGuiColor (self): return 'yellow'

	def getTemperature(self):
		return self.getInputChannel(self._inputId['temperature']).getValue()

	def setTemperature(self, value):
#		print(f'boiler: {value}')
		self.getInputChannel(self._inputId['temperature']).setValue(value)

	def getStage1(self):
		return self.getOutputChannel(self._outputId['burner1'])
	
	def getPump(self):
		return self.getOutputChannel(self._outputId['pump'])
		

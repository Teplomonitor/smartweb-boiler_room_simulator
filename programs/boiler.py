'''
@author: admin
'''

from .program import Program
from .program import InputInfo
from .program import OutputInfo
from gui.parameter import GuiParameter as GuiParameter

class Boiler(Program):
	'''
	classdocs
	'''

	@staticmethod
	def getType(): return 'BOILER'
	
	def initInputs(self):
		self._inputs['temperature'        ] = InputInfo(0, 'Т котла'       )
		self._inputs['backwardTemperature'] = InputInfo(1, 'Т обратки'     )
		self._inputs['outsideRequest'     ] = InputInfo(2, 'Внешний запрос')
		self._inputs['error'              ] = InputInfo(3, 'Ошибка котла'  )
		
	def initOutputs(self):
		self._outputs['pump'               ] = OutputInfo(0, 'Насос'           )
		self._outputs['burner1'            ] = OutputInfo(1, 'Ступень 1'       )
		self._outputs['burner2'            ] = OutputInfo(2, 'Ступень 2'       )
		self._outputs['power'              ] = OutputInfo(3, 'Мощность'        )
		self._outputs['temperature'        ] = OutputInfo(4, 'Температура'     )
		self._outputs['backwardTemperature'] = OutputInfo(5, 'Контроль обратки')

	def initGuiParameters(self):
		self._parameters['max_flow_rate'] = GuiParameter(3000, 'Расход'  , 0, 5000, 1, 'кг/ч')
		self._parameters['max_power'    ] = GuiParameter(  30, 'Мощность', 5,  300, 1, 'кВт')
		
	def __init__(self, preset):
		'''
		Constructor
		'''
		super().__init__(preset)
		
	def getGuiColor (self): return 'yellow'

	def getTemperature(self):
		return self.getInputChannel('temperature').getValue()

	def setTemperature(self, value):
#		print(f'boiler: {value}')
		self.getInputChannel('temperature').setValue(value)

	def getStage1(self):
		return self.getOutputChannel('burner1')
	
	def getPump(self):
		return self.getOutputChannel('pump')
		

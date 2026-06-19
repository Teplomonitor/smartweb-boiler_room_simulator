'''
@author: admin
'''

from .program import Program
from .program import InputInfo
from .program import OutputInfo
from gui.parameter import GuiParameter as GuiParameter

class HeatingCircuit(Program):
	'''
	classdocs
	'''
	@staticmethod
	def getType(): return 'HEATING_CIRCUIT'
	
	def getOutputTitles(self):
		return [
			'А.смеситель',
			'Смес. откр' ,
			'Смес. закр' ,
			'Насос'      ,
			'Клапан'     ,
			'Насос ТО'   ,
			'А. насос'   ,
			]
	
	def initInputs(self):
		self._inputs['temperature'        ] = InputInfo(0, 'Т подачи'          )
		self._inputs['thermostat'         ] = InputInfo(1, 'Термостат'         )
		self._inputs['outsideRequest'     ] = InputInfo(2, 'Внешний запрос'    )
		self._inputs['pumpControl'        ] = InputInfo(3, 'Управление насосом')
		self._inputs['backwardTemperature'] = InputInfo(4, 'Т обратки'         )
		
	def initOutputs(self):
		self._outputs['analogValve'   ] = OutputInfo(0, 'А.смеситель')
		self._outputs['tptValveOpen'  ] = OutputInfo(1, 'Смес. откр' )
		self._outputs['tptValveClose' ] = OutputInfo(2, 'Смес. закр' )
		self._outputs['pump'          ] = OutputInfo(3, 'Насос'      )
		self._outputs['thermomotor'   ] = OutputInfo(4, 'Клапан'     )
		self._outputs['heatchangePump'] = OutputInfo(5, 'Насос ТО'   )
		self._outputs['analogPump'    ] = OutputInfo(6, 'А. насос'   )

	def initGuiParameters(self):
		self._parameters['max_flow_rate'] = GuiParameter(1000, 'Расход', 0, 3000, 1, 'кг/ч')
		self._parameters['max_power'    ] = GuiParameter(3, 'Мощность', 0, 10, 1, 'кВт')
		
	def __init__(self, preset):
		'''
		Constructor
		'''
		super().__init__(preset)
		
	def getGuiColor (self): return 'green'


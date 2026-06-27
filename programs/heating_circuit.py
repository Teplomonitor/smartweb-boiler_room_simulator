'''
@author: admin
'''

from .program import Program
from .program import input_info
from .program import output_info
from gui.parameter import GuiParameter as GuiParameter

class HeatingCircuit(Program):
	'''
	classdocs
	'''
	@staticmethod
	def get_type(): return 'HEATING_CIRCUIT'
	
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
	
	def init_inputs(self):
		self._inputs['temperature'        ] = input_info(0, 'Т подачи'          )
		self._inputs['thermostat'         ] = input_info(1, 'Термостат'         )
		self._inputs['outsideRequest'     ] = input_info(2, 'Внешний запрос'    )
		self._inputs['pumpControl'        ] = input_info(3, 'Управление насосом')
		self._inputs['backwardTemperature'] = input_info(4, 'Т обратки'         )
		
	def init_outputs(self):
		self._outputs['analogValve'   ] = output_info(0, 'А.смеситель')
		self._outputs['tptValveOpen'  ] = output_info(1, 'Смес. откр' )
		self._outputs['tptValveClose' ] = output_info(2, 'Смес. закр' )
		self._outputs['pump'          ] = output_info(3, 'Насос'      )
		self._outputs['thermomotor'   ] = output_info(4, 'Клапан'     )
		self._outputs['heatchangePump'] = output_info(5, 'Насос ТО'   )
		self._outputs['analogPump'    ] = output_info(6, 'А. насос'   )

	def init_gui_parameters(self):
		self._parameters['max_flow_rate'] = GuiParameter(1000, 'Расход', 0, 3000, 1, 'кг/ч')
		self._parameters['max_power'    ] = GuiParameter(3, 'Мощность', 0, 10, 1, 'кВт')
		
	def __init__(self, preset):
		'''
		Constructor
		'''
		super().__init__(preset)
		
	def get_gui_color (self): return 'green'


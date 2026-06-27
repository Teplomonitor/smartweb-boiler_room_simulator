'''
@author: admin
'''

from .program import Program
from .program import InputInfo
from .program import OutputInfo
from gui.parameter import GuiParameter as GuiParameter

class Dhw(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return 'DHW'
	
	def init_inputs(self):
		self._inputs['temperature'        ] = InputInfo(0, 'Т бойлера')
		self._inputs['flow'               ] = InputInfo(1, 'Проток'   )
		self._inputs['backwardTemperature'] = InputInfo(2, 'Т обратки')
		
	def init_outputs(self):
		self._outputs['supplyPump'        ] = OutputInfo(0, 'Насос загрузки'   )
		self._outputs['circulationPump'   ] = OutputInfo(1, 'Цирк. насос'      )
		self._outputs['analogLoadingPump' ] = OutputInfo(2, 'А. насос загрузки')
		self._outputs['valveOpen'         ] = OutputInfo(3, 'Смес. откр'       )
		self._outputs['valveClose'        ] = OutputInfo(4, 'Смес. закр'       )

	def init_gui_parameters(self):
		self._parameters['max_flow_rate'] = GuiParameter(1000, 'Расход', 0, 3000, 1, 'кг/ч')
		self._parameters['max_power'    ] = GuiParameter(1, 'Мощность', 0, 10, 1, 'кВт')
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
				
	def get_gui_color (self): return 'orange'

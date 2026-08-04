'''
@author: admin
'''

from .program import Program
from .program import input_info
from .program import output_info
from gui.parameter import GuiParameter as GuiParameter
import smartnet.constants as snc

class Dhw(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return snc.ProgramType.DHW
	
	def init_inputs(self):
		self._inputs['temperature'        ] = input_info(0, 'Т бойлера')
		self._inputs['flow'               ] = input_info(1, 'Проток'   )
		self._inputs['backwardTemperature'] = input_info(2, 'Т обратки')
		
	def init_outputs(self):
		self._outputs['supplyPump'        ] = output_info(0, 'Насос загрузки'   )
		self._outputs['circulationPump'   ] = output_info(1, 'Цирк. насос'      )
		self._outputs['analogLoadingPump' ] = output_info(2, 'А. насос загрузки')
		self._outputs['valveOpen'         ] = output_info(3, 'Смес. откр'       )
		self._outputs['valveClose'        ] = output_info(4, 'Смес. закр'       )

	def init_gui_parameters(self):
		self._parameters['max_flow_rate'] = GuiParameter(1000, 'Расход', 0, 3000, 1, 'кг/ч')
		self._parameters['max_power'    ] = GuiParameter(1, 'Мощность', 0, 10, 1, 'кВт')
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
				
	def get_gui_color (self): return 'orange'

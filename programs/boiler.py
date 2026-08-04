'''
@author: admin
'''

from .program import Program
from .program import input_info
from .program import output_info
from gui.parameter import GuiParameter as GuiParameter

class Boiler(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return snc.ProgramType.BOILER
	
	def init_inputs(self):
		self._inputs['temperature'        ] = input_info(0, 'Т котла'       )
		self._inputs['backwardTemperature'] = input_info(1, 'Т обратки'     )
		self._inputs['outsideRequest'     ] = input_info(2, 'Внешний запрос')
		self._inputs['error'              ] = input_info(3, 'Ошибка котла'  )
		
	def init_outputs(self):
		self._outputs['pump'               ] = output_info(0, 'Насос'           )
		self._outputs['burner1'            ] = output_info(1, 'Ступень 1'       )
		self._outputs['burner2'            ] = output_info(2, 'Ступень 2'       )
		self._outputs['power'              ] = output_info(3, 'Мощность'        )
		self._outputs['temperature'        ] = output_info(4, 'Температура'     )
		self._outputs['backwardTemperature'] = output_info(5, 'Контроль обратки')

	def init_gui_parameters(self):
		self._parameters['max_flow_rate'] = GuiParameter(3000, 'Расход'  , 0, 5000, 1, 'кг/ч')
		self._parameters['max_power'    ] = GuiParameter(  30, 'Мощность', 5,  300, 1, 'кВт')
		
	def __init__(self, preset):
		'''
		Constructor
		'''
		super().__init__(preset)
		
	def get_gui_color (self): return 'yellow'

	def get_temperature(self):
		return self.get_input_channel('temperature').get_value()

	def set_temperature(self, value):
#		print(f'boiler: {value}')
		self.get_input_channel('temperature').set_value(value)

	def get_stage_1(self):
		return self.get_output_channel('burner1')
	
	def get_pump(self):
		return self.get_output_channel('pump')
		

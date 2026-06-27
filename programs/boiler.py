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
	def get_type(): return 'BOILER'
	
	def init_inputs(self):
		self._inputs['temperature'        ] = InputInfo(0, 'Т котла'       )
		self._inputs['backwardTemperature'] = InputInfo(1, 'Т обратки'     )
		self._inputs['outsideRequest'     ] = InputInfo(2, 'Внешний запрос')
		self._inputs['error'              ] = InputInfo(3, 'Ошибка котла'  )
		
	def init_outputs(self):
		self._outputs['pump'               ] = OutputInfo(0, 'Насос'           )
		self._outputs['burner1'            ] = OutputInfo(1, 'Ступень 1'       )
		self._outputs['burner2'            ] = OutputInfo(2, 'Ступень 2'       )
		self._outputs['power'              ] = OutputInfo(3, 'Мощность'        )
		self._outputs['temperature'        ] = OutputInfo(4, 'Температура'     )
		self._outputs['backwardTemperature'] = OutputInfo(5, 'Контроль обратки')

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
		return self.get_input_channel('temperature').getValue()

	def set_temperature(self, value):
#		print(f'boiler: {value}')
		self.get_input_channel('temperature').setValue(value)

	def get_stage_1(self):
		return self.get_output_channel('burner1')
	
	def get_pump(self):
		return self.get_output_channel('pump')
		

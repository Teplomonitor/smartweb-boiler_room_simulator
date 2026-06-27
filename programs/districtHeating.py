'''
@author: admin
'''

from .program import Program
from .program import input_info
from .program import output_info
from gui.parameter import GuiParameter as GuiParameter

class DistrictHeating(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return 'DISTRICT_HEATING'
	
	def init_inputs(self):
		self._inputs['supply_direct_temp'  ] = input_info(0, 'Подача из города')
		self._inputs['supply_backward_temp'] = input_info(1, 'Обратка в город' )
		self._inputs['direct_temp'         ] = input_info(2, 'Подача в дом'    )
		self._inputs['backward_temp'       ] = input_info(3, 'Обратка из дома' )
		self._inputs['thermal_output'      ] = input_info(4, 'Теплосчётчик'    )
		self._inputs['volume_flow'         ] = input_info(5, 'Расход'          )
		self._inputs['outside_request'     ] = input_info(6, 'Внешний запрос'  )
		
	def init_outputs(self):
		self._outputs['supply_pump'     ] = output_info(0, 'Насос загрузки')
		self._outputs['circulation_pump'] = output_info(1, 'Цирк. насос'   )
		self._outputs['valve'           ] = output_info(2, 'Клапан'        )
		self._outputs['analog_valve'    ] = output_info(3, 'А. клапан'     )

	def init_gui_parameters(self):
		self._parameters['max_flow_rate1'] = GuiParameter(3000, 'Расход в доме', 100, 6000, 1, 'кг/ч')
		self._parameters['max_flow_rate2'] = GuiParameter(3000, 'Расход в городе', 100, 6000, 1, 'кг/ч')
		self._parameters['max_power'     ] = GuiParameter(30, 'Мощность', 5, 300, 1, 'кВт')
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	
	def get_max_flow_rate1(self):
		return self._parameters['max_flow_rate1'].get_value()
	
	def get_max_flow_rate2(self):
		return self._parameters['max_flow_rate2'].get_value()

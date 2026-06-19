'''
@author: admin
'''

from .program import Program
from .program import InputInfo
from .program import OutputInfo
from gui.parameter import GuiParameter as GuiParameter

class DistrictHeating(Program):
	'''
	classdocs
	'''

	@staticmethod
	def getType(): return 'DISTRICT_HEATING'
	
	def initInputs(self):
		self._inputs['supply_direct_temp'  ] = InputInfo(0, 'Подача из города')
		self._inputs['supply_backward_temp'] = InputInfo(1, 'Обратка в город' )
		self._inputs['direct_temp'         ] = InputInfo(2, 'Подача в дом'    )
		self._inputs['backward_temp'       ] = InputInfo(3, 'Обратка из дома' )
		self._inputs['thermal_output'      ] = InputInfo(4, 'Теплосчётчик'    )
		self._inputs['volume_flow'         ] = InputInfo(5, 'Расход'          )
		self._inputs['outside_request'     ] = InputInfo(6, 'Внешний запрос'  )
		
	def initOutputs(self):
		self._outputs['supply_pump'     ] = OutputInfo(0, 'Насос загрузки')
		self._outputs['circulation_pump'] = OutputInfo(1, 'Цирк. насос'   )
		self._outputs['valve'           ] = OutputInfo(2, 'Клапан'        )
		self._outputs['analog_valve'    ] = OutputInfo(3, 'А. клапан'     )

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

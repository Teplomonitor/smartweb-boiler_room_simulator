'''
@author: admin
'''

from .program import Program
from .program import ParameterInfo as PI
from .program import InputInfo
from .program import OutputInfo
from gui.parameter import GuiParameter as GuiParameter

class SwimmingPool(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return 'POOL'

	_remoteControlParameters = {
		'requiredPoolTemperatureComfort' : PI('POOL', 'REQUIRED_POOL_TEMPERATURE'        ),
		'requiredPoolTemperatureEconom'  : PI('POOL', 'REQUIRED_POOL_TEMPERATURE_ECONOM' ),
		'currentRequiredPoolTemperature' : PI('POOL', 'CURRENT_REQUIRED_POOL_TEMPERATURE'),
		'workMode'                       : PI('POOL', 'WORK_MODE'                        ),
#		'schedule'                       : PI('POOL', 'SCHEDULE'                         ),
		'circulationPumpWorkMode'        : PI('POOL', 'CIRCULATION_PUMP_WORK_MODE'       ),
		'circulationPumpWorkPeriodOn'    : PI('POOL', 'CIRCULATION_PUMP_WORK_PERIOD_ON'  ),
		'circulationPumpWorkPeriodOff'   : PI('POOL', 'CIRCULATION_PUMP_WORK_PERIOD_OFF' ),
		'fillingDuration'                : PI('POOL', 'FILLING_DURATION'                 ),
		'lowWaterLevelAlarmReset'        : PI('POOL', 'LOW_WATER_LEVEL_ALARM_RESET'      ),
		'currentWorkModeStatus'          : PI('POOL', 'CURRENT_WORK_MODE_STATUS'         ),
		
		#TODO: add more parameters
	}
	
	def getParameterInfo(self, parameter): return self._remoteControlParameters[parameter]
	
	def init_inputs(self):
		self._inputs['poolTemperature'] = InputInfo(0, 'Т воды'        , -10, 50)
		self._inputs['outsideRequest' ] = InputInfo(1, 'Внешний запрос')
		self._inputs['waterLevel'     ] = InputInfo(2, 'Уровень воды'  )
		self._inputs['flow'           ] = InputInfo(3, 'Проток'        )
		
	def init_outputs(self):
		self._outputs['circulationPump'  ] = OutputInfo(0, 'Цирк. насос'         )
		self._outputs['loadingPump'      ] = OutputInfo(1, 'Насос загрузки'      )
		self._outputs['waterLevelControl'] = OutputInfo(2, 'Контроль уровня воды')
	
	def init_gui_parameters(self):
		self._parameters['max_flow_rate'] = GuiParameter(1000, 'Расход', 0, 3000, 1, 'кг/ч')
		self._parameters['max_power'    ] = GuiParameter(1, 'Мощность', 0, 10, 1, 'кВт')
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	def get_gui_color (self): return 'blue'
	
	def get_temperature         (self): return self.get_input_channel ('poolTemperature')
	def getCirculationPumpState(self): return self.get_output_channel('circulationPump')
	def getLoadingPumpState    (self): return self.get_output_channel('loadingPump')
	
	def set_temperature  (self, value): self.get_temperature().setValue(value)
	
	def setCirculationPumpWorkMode(self, value):
		workMode = {
			'CIRCULATION_ON'    : 0,
			'CIRCULATION_PROG'  : 1,
			'CIRCULATION_PERIOD': 2,
			'CIRCULATION_OFF'   : 3,
			}
		
		return self.writeParameterValue('circulationPumpWorkMode', workMode[value])
	
	

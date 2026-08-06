'''
@author: admin
'''

from .program import Program
from .program import input_info
from .program import output_info
from gui.parameter import GuiParameter as GuiParameter
import smartnet.constants as snc

class SwimmingPool(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return snc.ProgramType.POOL

	_remoteControlParameters = {
		'requiredPoolTemperatureComfort' : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.REQUIRED_POOL_TEMPERATURE        ),
		'requiredPoolTemperatureEconom'  : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.REQUIRED_POOL_TEMPERATURE_ECONOM ),
		'currentRequiredPoolTemperature' : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.CURRENT_REQUIRED_POOL_TEMPERATURE),
		'workMode'                       : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.WORK_MODE                        ),
		'schedule'                       : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.SCHEDULE                         ),
		'circulationPumpWorkMode'        : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_MODE       ),
		'circulationPumpWorkPeriodOn'    : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_PERIOD_ON  ),
		'circulationPumpWorkPeriodOff'   : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.CIRCULATION_PUMP_WORK_PERIOD_OFF ),
		'fillingDuration'                : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.FILLING_DURATION                 ),
		'lowWaterLevelAlarmReset'        : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.LOW_WATER_LEVEL_ALARM_RESET      ),
		'currentWorkModeStatus'          : (snc.ProgramType.POOL, snc.SwimmingPoolParameterId.CURRENT_WORK_MODE_STATUS         ),
		
		#TODO: add more parameters
	}
	
	def get_parameter_code(self, parameter): return self._remoteControlParameters[parameter]
	
	def init_inputs(self):
		self._inputs['poolTemperature'] = input_info(0, 'Т воды'        , -10, 50)
		self._inputs['outsideRequest' ] = input_info(1, 'Внешний запрос')
		self._inputs['waterLevel'     ] = input_info(2, 'Уровень воды'  )
		self._inputs['flow'           ] = input_info(3, 'Проток'        )
		
	def init_outputs(self):
		self._outputs['circulationPump'  ] = output_info(0, 'Цирк. насос'         )
		self._outputs['loadingPump'      ] = output_info(1, 'Насос загрузки'      )
		self._outputs['waterLevelControl'] = output_info(2, 'Контроль уровня воды')
	
	def init_gui_parameters(self):
		self._parameters['max_flow_rate'] = GuiParameter(1000, 'Расход', 0, 3000, 1, 'кг/ч')
		self._parameters['max_power'    ] = GuiParameter(1, 'Мощность', 0, 10, 1, 'кВт')
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	def get_gui_color (self): return 'blue'
	
	def get_temperature        (self): return self.get_input_channel ('poolTemperature')
	def getCirculationPumpState(self): return self.get_output_channel('circulationPump')
	def getLoadingPumpState    (self): return self.get_output_channel('loadingPump')
	
	def set_temperature  (self, value): self.get_temperature().set_value(value)
	
	def setCirculationPumpWorkMode(self, value):
		workMode = {
			'CIRCULATION_ON'    : 0,
			'CIRCULATION_PROG'  : 1,
			'CIRCULATION_PERIOD': 2,
			'CIRCULATION_OFF'   : 3,
			}
		
		return self.write_parameter_value('circulationPumpWorkMode', workMode[value])
	
	

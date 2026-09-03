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

	_remoteControlParameters = {
		'temperatureComfort': (snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_COMFORT),
		'temperatureDesired': (snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_DESIRED),
		'singleDhwMode': (snc.ProgramType.DHW, snc.DhwParameterId.SINGLE_DHW_MODE),
		'dhwRelief': (snc.ProgramType.DHW, snc.DhwParameterId.DHW_RELIEF),
		'circulationMode': (snc.ProgramType.DHW, snc.DhwParameterId.CIRCULATION_MODE),
		'circulationPeriodOn': (snc.ProgramType.DHW, snc.DhwParameterId.CIRCULATION_PERIOD_ON),
		'circulationPeriodOff': (snc.ProgramType.DHW, snc.DhwParameterId.CIRCULATION_PERIOD_OFF),
		'temperatureHysteresis': (snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_HYSTERESIS),
		'workMode': (snc.ProgramType.DHW, snc.DhwParameterId.WORK_MODE),
		'schedule': (snc.ProgramType.DHW, snc.DhwParameterId.SCHEDULE),
		'currentWorkModeStatus': (snc.ProgramType.DHW, snc.DhwParameterId.CURRENT_WORK_MODE_STATUS),
		'temperatureEconom': (snc.ProgramType.DHW, snc.DhwParameterId.TEMPERATURE_ECONOM),
		'location': (snc.ProgramType.DHW, snc.DhwParameterId.LOCATION),
		'alarmProgramId': (snc.ProgramType.CONSUMER, snc.ConsumerParameterId.ALARM_PROGRAM_ID),
	}

	def get_parameter_code(self, parameter):
		return self._remoteControlParameters[parameter]
	
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

	def get_temperature(self): return self.get_input_channel('temperature')
	def get_supply_pump_state(self): return self.get_output_channel('supplyPump')
	def get_circulation_pump_state(self): return self.get_output_channel('circulationPump')

	# Compatibility with the naming used by older simulator programs.
	def getSupplyPumpState(self): return self.get_supply_pump_state()
	def getCirculationPumpState(self): return self.get_circulation_pump_state()
				
	def get_gui_color (self): return 'orange'

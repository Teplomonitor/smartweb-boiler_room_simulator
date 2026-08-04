'''
@author: admin
'''

from .program import Program
from .program import input_info
from .program import output_info
from .program import ParameterInfo as PI
from gui.parameter import GuiParameter as GP
import smartnet.constants as snc

class Snowmelter(Program):
	'''
	classdocs
	'''
	@staticmethod
	def get_type(): return snc.ProgramType.SNOWMELT
	
	_remoteControlParameters = {
		'minOutdoorTemp'     : PI(snc.ProgramType.SNOWMELT, 'MINIMUM_OUTDOOR_TEMPERATURE'                            ),
		'maxOutdoorTemp'     : PI(snc.ProgramType.SNOWMELT, 'MAXIMUM_OUTDOOR_TEMPERATURE'                            ),
		'reqFlowTemp'        : PI(snc.ProgramType.SNOWMELT, 'REQUIRED_CONSTANT_FLOW_TEMPERATURE_OF_SECONDARY_CIRCUIT'),
		'outdoorTemp'        : PI(snc.ProgramType.SNOWMELT, 'OUTDOOR_TEMPERATURE'                                    ),
		'frostProtectionTemp': PI(snc.ProgramType.SNOWMELT, 'PRIMARY_CIRCUIT_PROTECTION_TEMPERATURE'                 ),
		'reqPlateTemp'       : PI(snc.ProgramType.SNOWMELT, 'REQUIRED_PLATE_TEMPERATURE'                             ),
		'alarmProgramId'     : PI(snc.ProgramType.CONSUMER, 'ALARM_PROGRAM_ID'                                       ),
		#TODO: add more parameters
	}
	
	def init_inputs(self):
		self._inputs['directFlowTemperature'] = input_info(0, 'Т подачи'     , -10, 100)
		self._inputs['backwardTemperature'  ] = input_info(1, 'Т обратки'    , -10, 100)
		self._inputs['plateTemperature'     ] = input_info(2, 'Т поверхности', -30,  40)
		self._inputs['snowSensor'           ] = input_info(3, 'Осадки'       )
		
	def init_outputs(self):
		self._outputs['primaryPump'            ] = output_info(0, 'Насос загрузки'   )
		self._outputs['secondaryPump'          ] = output_info(1, 'Цирк. насос'      )
		self._outputs['primaryPumpAnalogSignal'] = output_info(2, 'А. насос загрузки')

	def init_gui_parameters(self):
		self._parameters['max_flow_rate1'] = GP(1000, 'Расход до теплообменника', 0, 3000, 1, 'кг/ч')
		self._parameters['max_flow_rate2'] = GP(1000, 'Расход после теплообменника', 0, 3000, 1, 'кг/ч')
		self._parameters['max_power'     ] = GP(10, 'Мощность', 0, 30, 1, 'кВт')
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	def getDirectFlowTemperature  (self): return self.get_input_channel('directFlowTemperature')
	def getBackwardFlowTemperature(self): return self.get_input_channel('backwardTemperature'  )
	def getPlateTemperature       (self): return self.get_input_channel('plateTemperature'     )
	def getSnowSensor             (self): return self.get_input_channel('snowSensor'           )
	
	def getPrimaryPumpState  (self): return self.get_output_channel('primaryPump'            )
	def getSecondaryPumpState(self): return self.get_output_channel('secondaryPump'          )
	def getAnalogPumpSignal  (self): return self.get_output_channel('primaryPumpAnalogSignal')

	def setDirectFlowTemperature  (self, value): self.getDirectFlowTemperature  ().set_value(value)
	def setBackwardFlowTemperature(self, value): self.getBackwardFlowTemperature().set_value(value)
	def setPlateTemperature       (self, value): self.getPlateTemperature       ().set_value(value)
	def setSnowSensor             (self, value): self.getSnowSensor             ().set_value(value)

	def get_max_flow_rate1(self): return self._parameters['max_flow_rate1'].get_value()
	def get_max_flow_rate2(self): return self._parameters['max_flow_rate2'].get_value()
	
	def get_parameter_info(self, parameter):
		return self._remoteControlParameters[parameter]

	def get_gui_color (self): return 'blue'

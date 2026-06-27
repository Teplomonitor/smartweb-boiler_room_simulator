'''
@author: admin
'''

from .program import Program
from .program import InputInfo
from .program import OutputInfo
from .program import ParameterInfo as PI
from gui.parameter import GuiParameter as GP

class Snowmelter(Program):
	'''
	classdocs
	'''
	@staticmethod
	def get_type(): return 'SNOWMELT'
	
	_remoteControlParameters = {
		'minOutdoorTemp'     : PI('SNOWMELT', 'MINIMUM_OUTDOOR_TEMPERATURE'                            ),
		'maxOutdoorTemp'     : PI('SNOWMELT', 'MAXIMUM_OUTDOOR_TEMPERATURE'                            ),
		'reqFlowTemp'        : PI('SNOWMELT', 'REQUIRED_CONSTANT_FLOW_TEMPERATURE_OF_SECONDARY_CIRCUIT'),
		'outdoorTemp'        : PI('SNOWMELT', 'OUTDOOR_TEMPERATURE'                                    ),
		'frostProtectionTemp': PI('SNOWMELT', 'PRIMARY_CIRCUIT_PROTECTION_TEMPERATURE'                 ),
		'reqPlateTemp'       : PI('SNOWMELT', 'REQUIRED_PLATE_TEMPERATURE'                             ),
		'alarmProgramId'     : PI('CONSUMER', 'ALARM_PROGRAM_ID'                                       ),
		#TODO: add more parameters
	}
	
	def init_inputs(self):
		self._inputs['directFlowTemperature'] = InputInfo(0, 'Т подачи'     , -10, 100)
		self._inputs['backwardTemperature'  ] = InputInfo(1, 'Т обратки'    , -10, 100)
		self._inputs['plateTemperature'     ] = InputInfo(2, 'Т поверхности', -30,  40)
		self._inputs['snowSensor'           ] = InputInfo(3, 'Осадки'       )
		
	def init_outputs(self):
		self._outputs['primaryPump'            ] = OutputInfo(0, 'Насос загрузки'   )
		self._outputs['secondaryPump'          ] = OutputInfo(1, 'Цирк. насос'      )
		self._outputs['primaryPumpAnalogSignal'] = OutputInfo(2, 'А. насос загрузки')

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

	def setDirectFlowTemperature  (self, value): self.getDirectFlowTemperature  ().setValue(value)
	def setBackwardFlowTemperature(self, value): self.getBackwardFlowTemperature().setValue(value)
	def setPlateTemperature       (self, value): self.getPlateTemperature       ().setValue(value)
	def setSnowSensor             (self, value): self.getSnowSensor             ().setValue(value)

	def get_max_flow_rate1(self): return self._parameters['max_flow_rate1'].getValue()
	def get_max_flow_rate2(self): return self._parameters['max_flow_rate2'].getValue()
	
	def getParameterInfo(self, parameter):
		return self._remoteControlParameters[parameter]

	def get_gui_color (self): return 'blue'

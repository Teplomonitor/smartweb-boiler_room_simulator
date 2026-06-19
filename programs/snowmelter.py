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
	def getType(): return 'SNOWMELT'
	
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
	
	def initInputs(self):
		self._inputs['directFlowTemperature'] = InputInfo(0, 'Т подачи'     , -10, 100)
		self._inputs['backwardTemperature'  ] = InputInfo(1, 'Т обратки'    , -10, 100)
		self._inputs['plateTemperature'     ] = InputInfo(2, 'Т поверхности', -30,  40)
		self._inputs['snowSensor'           ] = InputInfo(3, 'Осадки'       )
		
	def initOutputs(self):
		self._outputs['primaryPump'            ] = OutputInfo(0, 'Насос загрузки'   )
		self._outputs['secondaryPump'          ] = OutputInfo(1, 'Цирк. насос'      )
		self._outputs['primaryPumpAnalogSignal'] = OutputInfo(2, 'А. насос загрузки')

	def initGuiParameters(self):
		self._parameters['max_flow_rate1'] = GP(1000, 'Расход до теплообменника', 0, 3000, 1, 'кг/ч')
		self._parameters['max_flow_rate2'] = GP(1000, 'Расход после теплообменника', 0, 3000, 1, 'кг/ч')
		self._parameters['max_power'     ] = GP(10, 'Мощность', 0, 30, 1, 'кВт')
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	def getDirectFlowTemperature  (self): return self.getInputChannel('directFlowTemperature')
	def getBackwardFlowTemperature(self): return self.getInputChannel('backwardTemperature'  )
	def getPlateTemperature       (self): return self.getInputChannel('plateTemperature'     )
	def getSnowSensor             (self): return self.getInputChannel('snowSensor'           )
	
	def getPrimaryPumpState  (self): return self.getOutputChannel('primaryPump'            )
	def getSecondaryPumpState(self): return self.getOutputChannel('secondaryPump'          )
	def getAnalogPumpSignal  (self): return self.getOutputChannel('primaryPumpAnalogSignal')

	def setDirectFlowTemperature  (self, value): self.getDirectFlowTemperature  ().setValue(value)
	def setBackwardFlowTemperature(self, value): self.getBackwardFlowTemperature().setValue(value)
	def setPlateTemperature       (self, value): self.getPlateTemperature       ().setValue(value)
	def setSnowSensor             (self, value): self.getSnowSensor             ().setValue(value)

	def getMaxFlowRate1(self): return self._parameters['max_flow_rate1'].getValue()
	def getMaxFlowRate2(self): return self._parameters['max_flow_rate2'].getValue()
	
	def getParameterInfo(self, parameter):
		return self._remoteControlParameters[parameter]

	def getGuiColor (self): return 'blue'

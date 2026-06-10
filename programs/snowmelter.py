'''
@author: admin
'''

from .program import Program
from .program import ParameterInfo as PI
from gui.parameter import GuiParameter

class Snowmelter(Program):
	'''
	classdocs
	'''

	def getType(self): return 'SNOWMELT'
	
	def getInputTitles(self):
		return [
			'Т подачи',
			'Т обратки',
			'Т поверхности',
			'Осадки',
			]

	def getOutputTitles(self):
		return [
			'Насос загрузки',
			'Цирк. насос',
			'А. насос загрузки',
			]

	_inputId = {
		'directFlowTemperature'  : 0,
		'backwardTemperature'    : 1,
		'plateTemperature'       : 2,
		'snowSensor'             : 3,
	}

	_outputId = {
		'primaryPump'              : 0,
		'secondaryPump'            : 1,
		'primaryPumpAnalogSignal'  : 2,
	}

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
	
	def initGuiParameters(self):
		rate = GuiParameter(1000, 'Расход до теплообменника')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		self._parameters['max_flow_rate1'] = rate
		
		rate = GuiParameter(1000, 'Расход после теплообменника')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		self._parameters['max_flow_rate2'] = rate
		
		power = GuiParameter(3, 'Мощность')
		power.setProperties(0, 30, 1, 'кВт')
		self._parameters['max_power']= power
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		inputsRange = [
			[-10, 100],
			[-10, 100],
			[-30,  40],
		]
		
		self.setInputsRange(inputsRange)
		

	def getDirectFlowTemperature(self):
		return self.getInputChannel(self._inputId['directFlowTemperature'])

	def setDirectFlowTemperature(self, value):
		self.getInputChannel(self._inputId['directFlowTemperature']).setValue(value)

	def getBackwardFlowTemperature(self):
		return self.getInputChannel(self._inputId['backwardTemperature'])
	
	def setBackwardFlowTemperature(self, value):
		self.getInputChannel(self._inputId['backwardTemperature']).setValue(value)

	def getPlateTemperature(self):
		return self.getInputChannel(self._inputId['plateTemperature'])

	def setPlateTemperature(self, value):
		self.getInputChannel(self._inputId['plateTemperature']).setValue(value)

	def getSnowSensor(self):
		return self.getInputChannel(self._inputId['snowSensor'])

	def setSnowSensor(self, value):
		self.getInputChannel(self._inputId['snowSensor']).setValue(value)
		
	def getPrimaryPumpState(self):
		return self.getOutputChannel(self._outputId['primaryPump'])

	def getSecondaryPumpState(self):
		return self.getOutputChannel(self._outputId['secondaryPump'])
	
	def getAnalogPumpSignal(self):
		return self.getOutputChannel(self._outputId['primaryPumpAnalogSignal'])
	
	def getMaxFlowRate1(self):
		return self._parameters['max_flow_rate1'].getValue()
	
	def getMaxFlowRate2(self):
		return self._parameters['max_flow_rate2'].getValue()
	
	def getParameterInfo(self, parameter):
		return self._remoteControlParameters[parameter]

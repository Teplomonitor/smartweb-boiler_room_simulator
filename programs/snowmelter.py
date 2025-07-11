'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter
from smartnet.remoteControl import RemoteControlParameter as RemoteControlParameter

class Snowmelter(Program):
	'''
	classdocs
	'''
			
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
		'minOutdoorTemp'     : {'programType': 'SNOWMELT', 'parameter': 'MINIMUM_OUTDOOR_TEMPERATURE'           , 'parameterType': 'TEMPERATURE'},
		'maxOutdoorTemp'     : {'programType': 'SNOWMELT', 'parameter': 'MAXIMUM_OUTDOOR_TEMPERATURE'           , 'parameterType': 'TEMPERATURE'},
		'reqPlateTemp'       : {'programType': 'SNOWMELT', 'parameter': 'REQUIRED_PLATE_TEMPERATURE'            , 'parameterType': 'TEMPERATURE'},
		'frostProtectionTemp': {'programType': 'SNOWMELT', 'parameter': 'PRIMARY_CIRCUIT_PROTECTION_TEMPERATURE', 'parameterType': 'TEMPERATURE'},
		#TODO: add more parameters
	}
	
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
		
		rate = GuiParameter(1000, 'Расход до теплообменника')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		self._parameters['max_flow_rate1'] = rate
		
		rate = GuiParameter(1000, 'Расход после теплообменника')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		self._parameters['max_flow_rate2'] = rate


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
	
	def readParameterValue(self, parameter):
		p = self._remoteControlParameters[parameter]
		remoteParam = RemoteControlParameter(parameterInfo = p, programId = self.getId() )
		remoteParam.read()
		
		return remoteParam.getValue()

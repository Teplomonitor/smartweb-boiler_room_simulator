'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class SwimmingPool(Program):
	'''
	classdocs
	'''

	_inputId = {
		'poolTemperature': 0,
		'outsideRequest' : 1,
		'waterLevel'     : 2,
		'flow'           : 3,
	}
	
	_outputId = {
		'circulationPump'  : 0,
		'loadingPump'      : 1,
		'waterLevelControl': 2,
	}

	_remoteControlParameters = {
		'requiredPoolTemperatureComfort' : {'programType': 'POOL', 'parameter': 'REQUIRED_POOL_TEMPERATURE'          , 'parameterType': 'TEMPERATURE'},
		'requiredPoolTemperatureEconom'  : {'programType': 'POOL', 'parameter': 'REQUIRED_POOL_TEMPERATURE_ECONOM'   , 'parameterType': 'TEMPERATURE'},
		'currentRequiredPoolTemperature' : {'programType': 'POOL', 'parameter': 'CURRENT_REQUIRED_POOL_TEMPERATURE'  , 'parameterType': 'TEMPERATURE'},
		'workMode'                       : {'programType': 'POOL', 'parameter': 'WORK_MODE'                          , 'parameterType': 'UINT8_T'},
#		'schedule'                       : {'programType': 'POOL', 'parameter': 'SCHEDULE'                           , 'parameterType': 'SCHEDULE'},
		'circulationPumpWorkMode'        : {'programType': 'POOL', 'parameter': 'CIRCULATION_PUMP_WORK_MODE'         , 'parameterType': 'UINT8_T'},
		'circulationPumpWorkPeriodOn'    : {'programType': 'POOL', 'parameter': 'CIRCULATION_PUMP_WORK_PERIOD_ON'    , 'parameterType': 'TIME_MS'},
		'circulationPumpWorkPeriodOff'   : {'programType': 'POOL', 'parameter': 'CIRCULATION_PUMP_WORK_PERIOD_OFF'   , 'parameterType': 'TIME_MS'},
		'fillingDuration'                : {'programType': 'POOL', 'parameter': 'FILLING_DURATION'                   , 'parameterType': 'TIME_MS'},
		'lowWaterLevelAlarmReset'        : {'programType': 'POOL', 'parameter': 'LOW_WATER_LEVEL_ALARM_RESET'        , 'parameterType': 'UINT8_T'},
		'currentWorkModeStatus'          : {'programType': 'POOL', 'parameter': 'CURRENT_WORK_MODE_STATUS'           , 'parameterType': 'UINT8_T'},
		
		#TODO: add more parameters
	}
	

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
				
		rate = GuiParameter(1000, 'Расход')
		rate.setProperties(0, 3000, 1, 'кг/ч')
		
		power = GuiParameter(1, 'Мощность')
		power.setProperties(0, 10, 1, 'кВт')
		
		self._parameters['max_flow_rate'] = rate
		self._parameters['max_power']= power
	
	def getMaxFlowRate(self):
		return self._parameters['max_flow_rate'].getValue()

	def getMaxPower(self):
		return self._parameters['max_power'].getValue()
	
	def getGuiColor (self): return 'blue'
	
	
	def getTemperature         (self): return self.getInputChannel (self. _inputId['poolTemperature'])
	def getCirculationPumpState(self): return self.getOutputChannel(self._outputId['circulationPump'])
	def getLoadingPumpState    (self): return self.getOutputChannel(self._outputId['loadingPump'])
	
	def setTemperature  (self, value): self.getInputChannel(self._inputId['poolTemperature']).setValue(value)
	
	def setCirculationPumpWorkMode(self, value):
		workMode = {
			'CIRCULATION_ON'    : 0,
			'CIRCULATION_PROG'  : 1,
			'CIRCULATION_PERIOD': 2,
			'CIRCULATION_OFF'   : 3,
			}
		
		return self.writeParameterValue('circulationPumpWorkMode', workMode[value])
	
	def getParameterInfo(self, parameter):
		return self._remoteControlParameters[parameter]
	

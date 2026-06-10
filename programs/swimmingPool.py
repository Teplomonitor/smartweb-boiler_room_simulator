'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class SwimmingPool(Program):
	'''
	classdocs
	'''

	def getType(self): return 'POOL'
	
	def getInputTitles(self):
		return [
			'Т воды',
			'Внешний запрос',
			'Уровень воды',
			'Проток',
			]

	def getOutputTitles(self):
		return [
			'Цирк. насос',
			'Насос загрузки',
			'Контроль уровня воды',
			]

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
		'requiredPoolTemperatureComfort' : {'programType': 'POOL', 'parameter': 'REQUIRED_POOL_TEMPERATURE'          },
		'requiredPoolTemperatureEconom'  : {'programType': 'POOL', 'parameter': 'REQUIRED_POOL_TEMPERATURE_ECONOM'   },
		'currentRequiredPoolTemperature' : {'programType': 'POOL', 'parameter': 'CURRENT_REQUIRED_POOL_TEMPERATURE'  },
		'workMode'                       : {'programType': 'POOL', 'parameter': 'WORK_MODE'                          },
#		'schedule'                       : {'programType': 'POOL', 'parameter': 'SCHEDULE'                           },
		'circulationPumpWorkMode'        : {'programType': 'POOL', 'parameter': 'CIRCULATION_PUMP_WORK_MODE'         },
		'circulationPumpWorkPeriodOn'    : {'programType': 'POOL', 'parameter': 'CIRCULATION_PUMP_WORK_PERIOD_ON'    },
		'circulationPumpWorkPeriodOff'   : {'programType': 'POOL', 'parameter': 'CIRCULATION_PUMP_WORK_PERIOD_OFF'   },
		'fillingDuration'                : {'programType': 'POOL', 'parameter': 'FILLING_DURATION'                   },
		'lowWaterLevelAlarmReset'        : {'programType': 'POOL', 'parameter': 'LOW_WATER_LEVEL_ALARM_RESET'        },
		'currentWorkModeStatus'          : {'programType': 'POOL', 'parameter': 'CURRENT_WORK_MODE_STATUS'           },
		
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
	

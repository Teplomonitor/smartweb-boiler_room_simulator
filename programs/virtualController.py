'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

PARAMETER_NUM = 16

class VirtualController(Program):
	'''
	classdocs
	'''

	_remoteControlParameters = {
		'controllerId'  : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'CONTROLLERID'},
		'sensorValue01' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR01'},
		'sensorValue02' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR02'},
		'sensorValue03' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR03'},
		'sensorValue04' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR04'},
		'sensorValue05' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR05'},
		'sensorValue06' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR06'},
		'sensorValue07' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR07'},
		'sensorValue08' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR08'},
		'sensorValue09' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR09'},
		'sensorValue10' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR10'},
		'sensorValue11' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR11'},
		'sensorValue12' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR12'},
		'sensorValue13' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR13'},
		'sensorValue14' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR14'},
		'sensorValue15' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR15'},
		'sensorValue16' : {'programType': 'VIRTUAL_CONTROLLER', 'parameter': 'SENSOR16'},
	}
	
	_sensors = [
		'sensorValue01',
		'sensorValue02',
		'sensorValue03',
		'sensorValue04',
		'sensorValue05',
		'sensorValue06',
		'sensorValue07',
		'sensorValue08',
		'sensorValue09',
		'sensorValue10',
		'sensorValue11',
		'sensorValue12',
		'sensorValue13',
		'sensorValue14',
		'sensorValue15',
		'sensorValue16',
		]

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		for i in range(0,PARAMETER_NUM):
			param = GuiParameter(30, f'Датчик {i+1}')
			param.setProperties(-30, 120, 0.1, 'у.е.')
			param.setOptions(['sin','freeze', 'other'])
			self._parameters[f'gui_sensor_value{i}'] = param
		
		
	def getParameterInfo(self, parameter):
		return self._remoteControlParameters[parameter]
	
	def getSensor(self, index):
		return self._parameters[f'gui_sensor_value{index}']
	
	def setSensor(self, index, value):
		self.writeParameterValue(self._sensors[index], value)
		return self.getSensor(index).setValue(value)

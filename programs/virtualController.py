'''
@author: admin
'''

from .program import Program
from .program import ParameterInfo as PI
from gui.parameter import GuiParameter as GuiParameter
import functions.periodicTrigger as pt

PARAMETER_NUM = 16

class VirtualController(Program):
	'''
	classdocs
	'''

	@staticmethod
	def getType(): return 'VIRTUAL_CONTROLLER'
	
	_remoteControlParameters = {
		'controllerId'  : PI('VIRTUAL_CONTROLLER', 'CONTROLLERID'),
		'sensorValue01' : PI('VIRTUAL_CONTROLLER', 'SENSOR01'),
		'sensorValue02' : PI('VIRTUAL_CONTROLLER', 'SENSOR02'),
		'sensorValue03' : PI('VIRTUAL_CONTROLLER', 'SENSOR03'),
		'sensorValue04' : PI('VIRTUAL_CONTROLLER', 'SENSOR04'),
		'sensorValue05' : PI('VIRTUAL_CONTROLLER', 'SENSOR05'),
		'sensorValue06' : PI('VIRTUAL_CONTROLLER', 'SENSOR06'),
		'sensorValue07' : PI('VIRTUAL_CONTROLLER', 'SENSOR07'),
		'sensorValue08' : PI('VIRTUAL_CONTROLLER', 'SENSOR08'),
		'sensorValue09' : PI('VIRTUAL_CONTROLLER', 'SENSOR09'),
		'sensorValue10' : PI('VIRTUAL_CONTROLLER', 'SENSOR10'),
		'sensorValue11' : PI('VIRTUAL_CONTROLLER', 'SENSOR11'),
		'sensorValue12' : PI('VIRTUAL_CONTROLLER', 'SENSOR12'),
		'sensorValue13' : PI('VIRTUAL_CONTROLLER', 'SENSOR13'),
		'sensorValue14' : PI('VIRTUAL_CONTROLLER', 'SENSOR14'),
		'sensorValue15' : PI('VIRTUAL_CONTROLLER', 'SENSOR15'),
		'sensorValue16' : PI('VIRTUAL_CONTROLLER', 'SENSOR16'),
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

	def initGuiParameters(self):
		for i in range(0,PARAMETER_NUM):
			param = GuiParameter(30, f'Датчик {i+1}', -30, 120, 0.1, 'у.е.')
			param.setOptions(['none'])
			self._parameters[f'gui_sensor_value{i}'] = param
		
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		self._reportPeriod = pt.PeriodicTrigger()
		
	def getSensorControlOption(self, index):
		return self.getSensor(index).getSelectedOption()
	
	def setSensorControlOptions(self, index, options):
		self.getSensor(index).setOptions(options)
		
	def getParameterInfo(self, parameter):
		return self._remoteControlParameters[parameter]
	
	def getSensor(self, index):
		return self._parameters[f'gui_sensor_value{index}']
	
	def getSensorValue(self, index):
		return self.getSensor(index).getValue()
	
	def setSensorValue(self, index, value):
		return self.getSensor(index).setValue(value)
	
	def reportSensorValue(self, index, value):
		#no confirm because we change value pretty often and it cause thread slowdown
		self.writeParameterValue(self._sensors[index], value, confirm = False)
	
	def setSensor(self, index, value):
		dT = value - self.getSensorValue(index)
		if (abs(dT) > 1) or self._reportPeriod.get(10):
			self._reportPeriod.reset()
			self.reportSensorValue(index, value)
			
		return self.setSensorValue(index, value)

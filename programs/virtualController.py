'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter
import functions.periodicTrigger as pt
import smartnet.constants as snc

PARAMETER_NUM = 16

class VirtualController(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return snc.ProgramType.VIRTUAL_CONTROLLER
	
	_remoteControlParameters = {
		'controllerId'  : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['CONTROLLERID']),
		'sensorValue01' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR01']),
		'sensorValue02' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR02']),
		'sensorValue03' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR03']),
		'sensorValue04' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR04']),
		'sensorValue05' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR05']),
		'sensorValue06' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR06']),
		'sensorValue07' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR07']),
		'sensorValue08' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR08']),
		'sensorValue09' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR09']),
		'sensorValue10' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR10']),
		'sensorValue11' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR11']),
		'sensorValue12' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR12']),
		'sensorValue13' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR13']),
		'sensorValue14' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR14']),
		'sensorValue15' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR15']),
		'sensorValue16' : (snc.ProgramType.VIRTUAL_CONTROLLER, snc.VirtualControllerParameterId['SENSOR16']),
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

	def init_gui_parameters(self):
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
		
	def get_parameter_code(self, parameter):
		return self._remoteControlParameters[parameter]
	
	def getSensor(self, index):
		return self._parameters[f'gui_sensor_value{index}']
	
	def getSensorValue(self, index):
		return self.getSensor(index).get_value()
	
	def set_sensor_value(self, index, value):
		return self.getSensor(index).set_value(value)
	
	def reportSensorValue(self, index, value):
		#no confirm because we change value pretty often and it cause thread slowdown
		self.write_parameter_value(self._sensors[index], value, confirm = False)
	
	def setSensor(self, index, value):
		dT = value - self.getSensorValue(index)
		if (abs(dT) > 1) or self._reportPeriod.get(10):
			self._reportPeriod.reset()
			self.reportSensorValue(index, value)
			
		return self.set_sensor_value(index, value)

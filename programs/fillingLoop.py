'''
@author: admin
'''

from .program import Program
from .program import input_info
from .program import output_info
import smartnet.constants as snc

class FillingLoop(Program):
	'''
	classdocs
	'''

	_remoteControlParameters = {
		'singleFill': (snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.SINGLE_FILL),
		'autoFill': (snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.AUTO_FILL),
		'pressureInputType': (snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.PRESSURE_INPUT_TYPE),
		'minimumPressure': (snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.MINIMUM_PRESSURE),
		'pressureHyst': (snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.PRESSURE_HYST),
		'fillingDuration': (snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.FILLING_DURATION),
		'pressureLossAlarmReset': (snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.PRESSURE_LOSS_ALARM_RESET),
		'autoFillCounter': (snc.ProgramType.FILLING_LOOP, snc.FillingLoopParameterId.AUTO_FILL_COUNTER),
	}

	def get_parameter_code(self, parameter):
		return self._remoteControlParameters[parameter]

	@staticmethod
	def get_type(): return snc.ProgramType.FILLING_LOOP

	def init_inputs(self):
		self._inputs['pressureSensor'      ] = input_info(0, 'Давление', 0, 10, 0.1, 'бар')
		
	def init_outputs(self):
		self._outputs['filling_loop_output'] = output_info(0, 'Подпитка'   )
		self._outputs['alarm_output'       ] = output_info(1, 'Авария'     )

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	def getPressure(self):
		return self.get_input_channel('pressureSensor')
	
	def get_gui_color (self): return 'blue'

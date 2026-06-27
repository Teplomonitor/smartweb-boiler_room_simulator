'''
@author: admin
'''

from .program import Program
from .program import input_info
from .program import output_info

class FillingLoop(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return 'FILLING_LOOP'

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

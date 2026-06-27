'''
@author: admin
'''

from .program import Program
from .program import InputInfo
from .program import OutputInfo

class FillingLoop(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return 'FILLING_LOOP'

	def init_inputs(self):
		self._inputs['pressureSensor'      ] = InputInfo(0, 'Давление', 0, 10, 0.1, 'бар')
		
	def init_outputs(self):
		self._outputs['filling_loop_output'] = OutputInfo(0, 'Подпитка'   )
		self._outputs['alarm_output'       ] = OutputInfo(1, 'Авария'     )

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	def getPressure(self):
		return self.get_input_channel('pressureSensor')
	
	def get_gui_color (self): return 'blue'

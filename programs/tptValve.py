'''
@author: admin
'''

from .program import input_info
from .program import output_info
from .program import Program

class TptValve(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return 'TPT_VALVE_ADAPTER'

	def init_inputs(self):
		self._inputs['signal'] = input_info(0, 'Управляющий сигнал')
		
	def init_outputs(self):
		self._outputs['valveOpen' ] = output_info(0, 'Смес. откр.')
		self._outputs['valveClose'] = output_info(1, 'Смес. закр.')

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)

		
	def getControlSignal   (self): return self.get_input_channel ('signal'    )
	def getValveOpenOutput (self): return self.get_output_channel('valveOpen' )
	def getValveCloseOutput(self): return self.get_output_channel('valveClose')
	
	def get_gui_color (self): return 'yellow'

'''
@author: admin
'''

from .program import InputInfo
from .program import OutputInfo
from .program import Program

class TptValve(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return 'TPT_VALVE_ADAPTER'

	def init_inputs(self):
		self._inputs['signal'] = InputInfo(0, 'Управляющий сигнал')
		
	def init_outputs(self):
		self._outputs['valveOpen' ] = OutputInfo(0, 'Смес. откр.')
		self._outputs['valveClose'] = OutputInfo(1, 'Смес. закр.')

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)

		
	def getControlSignal   (self): return self.get_input_channel ('signal'    )
	def getValveOpenOutput (self): return self.get_output_channel('valveOpen' )
	def getValveCloseOutput(self): return self.get_output_channel('valveClose')
	
	def get_gui_color (self): return 'yellow'

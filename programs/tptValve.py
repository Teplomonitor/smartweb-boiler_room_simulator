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
	def getType(): return 'TPT_VALVE_ADAPTER'

	def initInputs(self):
		self._inputs['signal'] = InputInfo(0, 'Управляющий сигнал')
		
	def initOutputs(self):
		self._outputs['valveOpen' ] = OutputInfo(0, 'Смес. откр.')
		self._outputs['valveClose'] = OutputInfo(1, 'Смес. закр.')

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)

		
	def getControlSignal   (self): return self.getInputChannel ('signal'    )
	def getValveOpenOutput (self): return self.getOutputChannel('valveOpen' )
	def getValveCloseOutput(self): return self.getOutputChannel('valveClose')
	
	def getGuiColor (self): return 'yellow'

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
	def getType(): return 'FILLING_LOOP'

	def initInputs(self):
		self._inputs['pressureSensor'      ] = InputInfo(0, 'Давление', 0, 10, 0.1, 'бар')
		
	def initOutputs(self):
		self._outputs['filling_loop_output'] = OutputInfo(0, 'Подпитка'   )
		self._outputs['alarm_output'       ] = OutputInfo(1, 'Авария'     )

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
	def getPressure(self):
		return self.getInputChannel('pressureSensor')
	
	def getGuiColor (self): return 'blue'

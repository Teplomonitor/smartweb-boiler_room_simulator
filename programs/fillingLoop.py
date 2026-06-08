'''
@author: admin
'''

from .program import Program

class FillingLoop(Program):
	'''
	classdocs
	'''

	def getType(self): return 'FILLING_LOOP'
	
	def getInputTitles(self):
		return [
			'Давление',
			]

	def getOutputTitles(self):
		return [
			'Подпитка',
			'Авария',
			]
		
	_inputId = {
		'pressureSensor'  : 0,
	}
	
	_outputId = {
		'filling_loop_output' : 0,
		'alarm_output'        : 1,
	}

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)

		self.getPressure().setProperties(0, 10, 0.1, 'бар')
		
		
	def getPressure(self):
		return self.getInputChannel(self._inputId['pressureSensor'])
	
	def getGuiColor (self): return 'blue'

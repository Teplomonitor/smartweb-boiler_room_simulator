'''
@author: admin
'''

from .program import Program

class TptValve(Program):
	'''
	classdocs
	'''

	def getType(self): return 'TPT_VALVE_ADAPTER'
	
	def getInputTitles(self):
		return [
			'Управляющий сигнал',
			]

	def getOutputTitles(self):
		return [
			'Смес. откр.',
			'Смес. закр.',
			]
		
	_inputId = {
		'signal'  : 0,
	}

	_outputId = {
		'valveOpen' : 0,
		'valveClose': 1,
	}

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)

		
	def getControlSignal   (self): return self.getInputChannel (self._inputId['signal'])
	def getValveOpenOutput (self): return self.getOutputChannel(self._outputId['valveOpen'])
	def getValveCloseOutput(self): return self.getOutputChannel(self._outputId['valveClose'])
	
	def getGuiColor (self): return 'yellow'

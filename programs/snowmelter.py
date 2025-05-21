'''
@author: admin
'''

from .program import Program

class Snowmelter(Program):
	'''
	classdocs
	'''

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		inputsRange = [
			[-10, 100],
			[-10,  100],
			[-30,   40],
		]
		
		self.setInputsRange(inputsRange)
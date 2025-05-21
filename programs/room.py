'''
@author: admin
'''

from .program import Program

class Room(Program):
	'''
	classdocs
	'''

	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		inputsRange = [
			[-10, 50],
			None,
			[-10,   70],
			[-10,   70],
			[  0,  100],
			[  0, 2000],
		]
		
		self.setInputsRange(inputsRange)

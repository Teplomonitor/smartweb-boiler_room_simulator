'''
@author: admin
'''

from .program import Program

class Oat(Program):
	'''
	classdocs
	'''


	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		
		inputsRange = [
			[-40, 40],
		]
		
		self.setInputsRange(inputsRange)

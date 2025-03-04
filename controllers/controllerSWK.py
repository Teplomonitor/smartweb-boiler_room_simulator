'''
@author: admin
'''

from .controller import Controller

class SWK(Controller):
	'''
	classdocs
	'''


	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(self, params)
		
	
	def getOutputsNum(self):
		return 5
	
	def getInputsNum(self):
		return 6
		
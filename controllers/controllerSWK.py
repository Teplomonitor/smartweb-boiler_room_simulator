'''
@author: admin
'''

from .controller import Controller

class SWK(Controller):
	'''
	classdocs
	'''


	def __init__(self, controllerId, bus):
		'''
		Constructor
		'''
		super().__init__(controllerId, bus)
		
	
	def getOutputsNum(self):
		return 5
	
	def getInputsNum(self):
		return 6
		
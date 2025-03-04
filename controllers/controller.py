'''
Created on 4 мар. 2025 г.

@author: admin
'''

class Controller(object):
	'''
	classdocs
	'''


	def __init__(self, params):
		'''
		Constructor
		'''
		self.controllerId = params['CONTROLLER_ID']
		
	
	def addProgram(self, programType, programId):
		pass
	
	def getOutputsNum(self):
		return 0
	
	def getInputsNum(self):
		return 0
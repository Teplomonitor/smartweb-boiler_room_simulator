'''
@author: admin
'''

class Program(object):
	'''
	classdocs
	'''

	def __init__(self, programType, programId, programScheme = 'DEFAULT'):
		'''
		Constructor
		'''
		
		self._type    = programType
		self._id      = programId
		self._scheme  = programScheme
		self._title   = None
		self._inputs  = []
		self._outputs = []
		
'''
@author: admin
'''

from .program import Program
from .program import InputInfo

class Cascade(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return 'CASCADE_MANAGER'
	
	def init_inputs(self):
		self._inputs['temperature'   ] = InputInfo(0, 'Коллектор'     )
		self._inputs['outsideRequest'] = InputInfo(1, 'Внешний запрос')
		
	def __init__(self, preset):
		'''
		Constructor
		'''
		super().__init__(preset)
	
	def getCascadeManagerSourceList(self):
		preset = self.get_preset()
		settings = preset.getSettings().get()
		
		sourceList = [0, 0, 0, 0, 0, 0, 0, 0]
		for setting in settings:
			if setting.get_program_type() == 'CASCADE_MANAGER':
				if setting.get_parameter_idCode() == 'PARAM_TEMPERATURE_SOURCE_ID':
					sourceList[setting.getParameterIndex()] = setting.getValue()
		
		return sourceList
	
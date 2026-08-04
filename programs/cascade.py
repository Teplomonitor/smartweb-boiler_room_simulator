'''
@author: admin
'''

from .program import Program
from .program import input_info
import smartnet.constants as snc

class Cascade(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return snc.ProgramType.CASCADE_MANAGER
	
	def init_inputs(self):
		self._inputs['temperature'   ] = input_info(0, 'Коллектор'     )
		self._inputs['outsideRequest'] = input_info(1, 'Внешний запрос')
		
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
			if setting.get_program_type() == snc.ProgramType.CASCADE_MANAGER:
				if setting.get_parameter_id() == snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID:
					sourceList[setting.getParameterIndex()] = setting.get_value()
		
		return sourceList
	
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
	def getType(): return 'CASCADE_MANAGER'
	
	def initInputs(self):
		self._inputs['temperature'   ] = InputInfo(0, 'Коллектор'     )
		self._inputs['outsideRequest'] = InputInfo(1, 'Внешний запрос')
		
	def __init__(self, preset):
		'''
		Constructor
		'''
		super().__init__(preset)
	
	def getCascadeManagerSourceList(self):
		preset = self.getPreset()
		settings = preset.getSettings().get()
		
		sourceList = [0, 0, 0, 0, 0, 0, 0, 0]
		for setting in settings:
			if setting.getProgramType() == 'CASCADE_MANAGER':
				if setting.getParameterIdCode() == 'PARAM_TEMPERATURE_SOURCE_ID':
					sourceList[setting.getParameterIndex()] = setting.getValue()
		
		return sourceList
	
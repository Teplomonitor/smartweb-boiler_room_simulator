'''
@author: admin
'''

from .program import Program

class Cascade(Program):
	'''
	classdocs
	'''

	def getType(self): return 'CASCADE_MANAGER'
	
	def getInputTitles(self):
		return [
			'Коллектор',
			'Внешний запрос',
			]

	def getOutputTitles(self):
		return [
			]


	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
	
	def getCascadeManagerSourceList(self):
		preset = self.getPreset()
		settings = preset.getSettings().get()
		
		sourceList = [0, 0, 0, 0, 0, 0, 0, 0]
		for setting in settings:
			if setting.getProgramType() == 'CASCADE_MANAGER':
				if setting.getParameterIdCode() == 'PARAM_TEMPERATURE_SOURCE_ID':
					sourceList[setting.getParameterIndex()] = setting.getValue()
		
		return sourceList
	
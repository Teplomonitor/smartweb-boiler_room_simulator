'''
@author: admin
'''

from .program import Program
from gui.parameter import GuiParameter as GuiParameter

class Room(Program):
	'''
	classdocs
	'''

	def getType(self): return 'ROOM_DEVICE'
	
	def getInputTitles(self):
		return [
			'Т помещения',
			'Режим',
			'Т пола',
			'Т стены',
			'Влажность',
			'CO2',
			'Движение',
			]

	def getOutputTitles(self):
		return [
			'Клапан ТП',
			'Клапан РО',
			'Клапан ДН',
			'Сигнал ТП',
			'Сигнал РО',
			'Сигнал ДН',
			'Вентиляция',
			]

	def initGuiParameters(self):
		power = GuiParameter(1, 'Мощность')
		power.setProperties(0, 10, 1, 'кВт')
		
		self._parameters['max_power']= power
	
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

	def getRoomTemperatureSourceList(self):
		preset = self.getPreset()
		settings = preset.getSettings().get()
		
		circuitList = [0, 0, 0]
		
		for setting in settings:
			if setting.getProgramType() == 'ROOM_DEVICE':
				if setting.getParameterIdCode() == 'RESPONSIBLE_CIRCUIT_1':
					circuitList[0] = setting.getValue()
				if setting.getParameterIdCode() == 'RESPONSIBLE_CIRCUIT_2':
					circuitList[1] = setting.getValue()
				if setting.getParameterIdCode() == 'RESPONSIBLE_CIRCUIT_3':
					circuitList[2] = setting.getValue()
		return circuitList
	
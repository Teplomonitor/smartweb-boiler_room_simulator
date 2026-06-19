'''
@author: admin
'''

from .program import Program
from .program import InputInfo
from .program import OutputInfo
from gui.parameter import GuiParameter as GuiParameter

class Room(Program):
	'''
	classdocs
	'''

	@staticmethod
	def getType(): return 'ROOM_DEVICE'
	
	def initInputs(self):
		self._inputs['roomTemperature' ] = InputInfo(0, 'Т помещения', -10,   50)
		self._inputs['mode_deprecated' ] = InputInfo(1, 'Режим'                 )
		self._inputs['floorTemperature'] = InputInfo(2, 'Т пола'     , -10,   70)
		self._inputs['wallTemperature' ] = InputInfo(3, 'Т стены'    , -10,   70)
		self._inputs['humidity'        ] = InputInfo(4, 'Влажность'  ,   0,  100)
		self._inputs['CO2'             ] = InputInfo(5, 'CO2'        ,   0, 2000)
		self._inputs['motion'          ] = InputInfo(6, 'Движение'              )
		
	def initOutputs(self):
		self._outputs['valve1'      ] = OutputInfo(0, 'Клапан ТП' )
		self._outputs['valve2'      ] = OutputInfo(1, 'Клапан РО' )
		self._outputs['valve3'      ] = OutputInfo(2, 'Клапан ДН' )
		self._outputs['analogValve1'] = OutputInfo(3, 'Сигнал ТП' )
		self._outputs['analogValve2'] = OutputInfo(4, 'Сигнал РО' )
		self._outputs['analogValve3'] = OutputInfo(5, 'Сигнал ДН' )
		self._outputs['ventilation' ] = OutputInfo(6, 'Вентиляция')

	def initGuiParameters(self):
		self._parameters['max_power']= GuiParameter(1, 'Мощность', 0, 10, 1, 'кВт')
	
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		

	def getTemperature(self): return self.getInputChannel('roomTemperature').getValue()

	def setTemperature(self, value): self.getInputChannel('roomTemperature').setValue(value)

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
	
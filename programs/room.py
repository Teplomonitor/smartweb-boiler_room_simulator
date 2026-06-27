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
	def get_type(): return 'ROOM_DEVICE'
	
	def init_inputs(self):
		self._inputs.update({
			'roomTemperature' : InputInfo(0, 'Т помещения', -10,   50),
			'mode_deprecated' : InputInfo(1, 'Режим'                 ),
			'floorTemperature': InputInfo(2, 'Т пола'     , -10,   70),
			'wallTemperature' : InputInfo(3, 'Т стены'    , -10,   70),
			'humidity'        : InputInfo(4, 'Влажность'  ,   0,  100),
			'CO2'             : InputInfo(5, 'CO2'        ,   0, 2000),
			'motion'          : InputInfo(6, 'Движение'              ),
		})
		
	def init_outputs(self):
		self._outputs.update({
			'valve1'      : OutputInfo(0, 'Клапан ТП' ),
			'valve2'      : OutputInfo(1, 'Клапан РО' ),
			'valve3'      : OutputInfo(2, 'Клапан ДН' ),
			'analogValve1': OutputInfo(3, 'Сигнал ТП' ),
			'analogValve2': OutputInfo(4, 'Сигнал РО' ),
			'analogValve3': OutputInfo(5, 'Сигнал ДН' ),
			'ventilation' : OutputInfo(6, 'Вентиляция'),
		})

	def init_gui_parameters(self):
		self._parameters['max_power']= GuiParameter(1, 'Мощность', 0, 10, 1, 'кВт')
	
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		

	def get_temperature(self): return self.get_input_channel('roomTemperature')

	def set_temperature(self, value): self.get_temperature().setValue(value)

	def getRoomTemperatureSourceList(self):
		preset = self.get_preset()
		settings = preset.getSettings().get()
		
		circuitList = [0, 0, 0]
		
		for setting in settings:
			if setting.get_program_type() == 'ROOM_DEVICE':
				parameterIdCode = setting.get_parameter_idCode()
				parameterValue  = setting.getValue()
				if   parameterIdCode == 'RESPONSIBLE_CIRCUIT_1': circuitList[0] = parameterValue
				elif parameterIdCode == 'RESPONSIBLE_CIRCUIT_2': circuitList[1] = parameterValue
				elif parameterIdCode == 'RESPONSIBLE_CIRCUIT_3': circuitList[2] = parameterValue
		return circuitList
	

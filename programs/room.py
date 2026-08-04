'''
@author: admin
'''

from .program import Program
from .program import input_info
from .program import output_info
from gui.parameter import GuiParameter as GuiParameter
import smartnet.constants as snc

class Room(Program):
	'''
	classdocs
	'''

	@staticmethod
	def get_type(): return snc.ProgramType.ROOM_DEVICE
	
	def init_inputs(self):
		self._inputs.update({
			'roomTemperature' : input_info(0, 'Т помещения', -10,   50),
			'mode_deprecated' : input_info(1, 'Режим'                 ),
			'floorTemperature': input_info(2, 'Т пола'     , -10,   70),
			'wallTemperature' : input_info(3, 'Т стены'    , -10,   70),
			'humidity'        : input_info(4, 'Влажность'  ,   0,  100),
			'CO2'             : input_info(5, 'CO2'        ,   0, 2000),
			'motion'          : input_info(6, 'Движение'              ),
		})
		
	def init_outputs(self):
		self._outputs.update({
			'valve1'      : output_info(0, 'Клапан ТП' ),
			'valve2'      : output_info(1, 'Клапан РО' ),
			'valve3'      : output_info(2, 'Клапан ДН' ),
			'analogValve1': output_info(3, 'Сигнал ТП' ),
			'analogValve2': output_info(4, 'Сигнал РО' ),
			'analogValve3': output_info(5, 'Сигнал ДН' ),
			'ventilation' : output_info(6, 'Вентиляция'),
		})

	def init_gui_parameters(self):
		self._parameters['max_power']= GuiParameter(1, 'Мощность', 0, 10, 1, 'кВт')
	
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		

	def get_temperature(self): return self.get_input_channel('roomTemperature')

	def set_temperature(self, value): self.get_temperature().set_value(value)

	def getRoomTemperatureSourceList(self):
		preset = self.get_preset()
		settings = preset.getSettings().get()
		
		circuitList = [0, 0, 0]
		
		for setting in settings:
			if setting.get_program_type() == snc.ProgramType.ROOM_DEVICE:
				parameterId = setting.get_parameter_id()
				if   parameterId == snc.RoomDeviceParameterId['RESPONSIBLE_CIRCUIT_1']: circuitList[0] = setting.get_value()
				elif parameterId == snc.RoomDeviceParameterId['RESPONSIBLE_CIRCUIT_2']: circuitList[1] = setting.get_value()
				elif parameterId == snc.RoomDeviceParameterId['RESPONSIBLE_CIRCUIT_3']: circuitList[2] = setting.get_value()
		return circuitList
	

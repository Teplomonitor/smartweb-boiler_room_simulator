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
		self._parameters['volume'] = GuiParameter(150, 'Объём помещения', 1, 3000, 1, 'м³')
		self._parameters['thermal_capacity'] = GuiParameter(3000, 'Теплоёмкость помещения', 1, 50000, 100, 'кДж/К')
		self._parameters['humidity_generation'] = GuiParameter(1, 'Прирост влажности без вентиляции', 0, 50, 0.1, '%/ч')
	
	def __init__(self, params):
		'''
		Constructor
		'''
		super().__init__(params)
		

	def get_temperature(self): return self.get_input_channel('roomTemperature')

	def set_temperature(self, value): self.get_temperature().set_value(value)

	def getRoomTemperatureSourceList(self):
		return [self.get_preset_setting(parameter_id) for parameter_id in (
			snc.RoomDeviceParameterId.RESPONSIBLE_CIRCUIT_1,
			snc.RoomDeviceParameterId.RESPONSIBLE_CIRCUIT_2,
			snc.RoomDeviceParameterId.RESPONSIBLE_CIRCUIT_3,
		)]

	def get_preset_setting(self, parameter_id, default=0):
		preset = self.get_preset()
		settings = preset.getSettings() if preset is not None else None
		if settings is not None:
			for setting in settings.get():
				if (setting.get_program_type() == snc.ProgramType.ROOM_DEVICE
					and setting.get_parameter_id() == parameter_id
					and setting.get_value() is not None):
					return setting.get_value()
		return default

	def get_ventilation_id(self):
		return self.get_preset_setting(snc.RoomDeviceParameterId.VENTILATION_CIRCUIT)
	

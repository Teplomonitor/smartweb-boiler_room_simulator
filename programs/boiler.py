'''
@author: admin
'''

from .program import Program
from .program import input_info
from .program import output_info
from gui.parameter import GuiParameter as GuiParameter
import smartnet.constants as snc

class Boiler(Program):
	'''
	classdocs
	'''

	_remoteControlParameters = {
		'maximumTemperature': (
			snc.ProgramType.TEMPERATURE_GENERATOR,
			snc.TemperatureGeneratorParameterId.MAXIMUM_TEMPERATURE,
		),
		'minimumTemperature': (
			snc.ProgramType.TEMPERATURE_GENERATOR,
			snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE,
		),
		'minimumTemperatureRestriction': (
			snc.ProgramType.TEMPERATURE_GENERATOR,
			snc.TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION,
		),
		'pumpOffDelay': (
			snc.ProgramType.TEMPERATURE_GENERATOR,
			snc.TemperatureGeneratorParameterId.PUMP_OFF_DELAY,
		),
	}

	@staticmethod
	def get_type(): return snc.ProgramType.BOILER

	def get_parameter_code(self, parameter):
		return self._remoteControlParameters[parameter]

	def init_inputs(self):
		self._inputs['temperature'        ] = input_info(0, 'Т котла'       )
		self._inputs['backwardTemperature'] = input_info(1, 'Т обратки'     )
		self._inputs['outsideRequest'     ] = input_info(2, 'Внешний запрос')
		self._inputs['error'              ] = input_info(3, 'Ошибка котла'  )

	def init_outputs(self):
		self._outputs['pump'               ] = output_info(0, 'Насос'           )
		self._outputs['burner1'            ] = output_info(1, 'Ступень 1'       )
		self._outputs['burner2'            ] = output_info(2, 'Ступень 2'       )
		self._outputs['power'              ] = output_info(3, 'Мощность'        )
		self._outputs['temperature'        ] = output_info(4, 'Температура'     )
		self._outputs['backwardTemperature'] = output_info(5, 'Контроль обратки')

	def init_gui_parameters(self):
		self._parameters['max_flow_rate'] = GuiParameter(3000, 'Расход'  , 0, 5000, 1, 'кг/ч')
		self._parameters['max_power'    ] = GuiParameter(  30, 'Мощность', 5,  300, 1, 'кВт')
		# Used only with a discrete first stage and a modulating second stage.
		self._parameters['stage_1_power_percent'] = GuiParameter(50, 'Доля ступени 1', 0, 100, 1, '%')

	def __init__(self, preset):
		'''
		Constructor
		'''
		super().__init__(preset)

	def get_gui_color(self): return 'yellow'

	def get_temperature(self):
		return self.get_input_channel('temperature').get_value()

	def set_temperature(self, value):
		self.get_input_channel('temperature').set_value(value)

	def get_stage_1(self):
		return self.get_output_channel('burner1')

	def get_power_output(self):
		return self.get_output_channel('power')

	def get_power_output_percent(self):
		output = self.get_power_output()
		if not output.is_mapped():
			return None
		signal = output.get_value()
		if signal is None:
			return None
		# SmartWeb: OFF=0, analog range=1..254, discrete ON=255.
		return max(0.0, min(100.0, (signal - 1) * 100.0 / 253))

	def get_stage_1_power_percent(self):
		return self._parameters['stage_1_power_percent'].get_value()

	def get_pump(self):
		return self.get_output_channel('pump')

	def get_pump_state(self):
		pump = self.get_pump()
		if pump is None:
			return None
		return pump.get_value()

	def get_pump_off_delay(self):
		return self.read_parameter_value('pumpOffDelay')

	def get_maximum_temperature(self):
		return self.read_parameter_value('maximumTemperature')

	def get_minimum_temperature(self):
		return self.read_parameter_value('minimumTemperature')

	def get_minimum_temperature_restriction(self):
		return self.read_parameter_value('minimumTemperatureRestriction')

	def set_pump_off_delay(self, value):
		return self.write_parameter_value('pumpOffDelay', value)


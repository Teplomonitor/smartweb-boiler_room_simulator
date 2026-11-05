import smartnet.constants as snc

from .program import Program, input_info, output_info


class DoublePump(Program):
	@staticmethod
	def get_type():
		return snc.ProgramType.DOUBLE_PUMP

	def init_inputs(self):
		self._inputs['control'] = input_info(0, 'Управляющий сигнал', 0, 100, 1, '%')
		self._inputs['flow'] = input_info(1, 'Датчик протока', 0, 1, 1, '')
		self._inputs['pump_1_error'] = input_info(2, 'Авария насоса 1', 0, 1, 1, '')
		self._inputs['pump_2_error'] = input_info(3, 'Авария насоса 2', 0, 1, 1, '')

	def init_outputs(self):
		self._outputs['discrete_pump_1'] = output_info(0, 'Насос 1 (дискретный)')
		self._outputs['discrete_pump_2'] = output_info(1, 'Насос 2 (дискретный)')
		self._outputs['analog_pump_1'] = output_info(2, 'Насос 1 (аналоговый)')
		self._outputs['analog_pump_2'] = output_info(3, 'Насос 2 (аналоговый)')
		self._outputs['alarm'] = output_info(4, 'Общая авария')

	def __init__(self, preset):
		super().__init__(preset)
		for channel in self._inputs.values():
			channel.set_value(0)
			channel.set_value('open')

	def is_any_pump_running(self):
		for name in ('discrete_pump_1', 'discrete_pump_2', 'analog_pump_1', 'analog_pump_2'):
			channel = self.get_output_channel(name)
			if channel.is_mapped():
				value = channel.get_value()
				if value is not None and value > 0:
					return True
		return False
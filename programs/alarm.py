import smartnet.constants as snc

from .program import Program, input_info


class Alarm(Program):
	@staticmethod
	def get_type():
		return snc.ProgramType.ALARM

	def init_inputs(self):
		for index in range(8):
			self._inputs[f'input_{index + 1}'] = input_info(
				index, f'Вход {index + 1}', -40, 150, 0.1)
		self._inputs['alarm_reset'] = input_info(8, 'Общий сброс тревог', 0, 1, 1, '')

	def __init__(self, preset):
		super().__init__(preset)
		for channel in self._inputs.values():
			channel.setOpen(True)

	def get_alarm_input(self, index):
		return self.get_input_channel(f'input_{index + 1}')

	def get_reset_input(self):
		return self.get_input_channel('alarm_reset')
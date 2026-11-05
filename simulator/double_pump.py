class Simulator(object):
	def __init__(self, program, control):
		self._program = program

	def run(self):
		flow = self._program.get_input_channel('flow')
		flow.set_value('short' if self._program.is_any_pump_running() else 'open')
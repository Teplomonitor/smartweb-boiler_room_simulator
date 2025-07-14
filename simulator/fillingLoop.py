
class Simulator(object):
	def __init__(self, program, control):
		self._program    = program

		self.setPressure(3)

	def getPressure(self):
		return self._program.getPressure().getValue()

	def setPressure(self, value):
		self._program.getPressure().setValue(value)

	def computePressure(self):
		pressure  = self.getPressure()
		return pressure

	def run(self):
		self.setPressure(self.computePressure())

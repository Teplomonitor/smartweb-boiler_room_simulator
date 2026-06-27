
import math
import time

VIRTUAL_SENSORS_MAX_NUM = 16

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._time_start = time.time()
		self._control    = control

		for i in range(0,VIRTUAL_SENSORS_MAX_NUM):
			self.setSensor(i, 20 + i*5)
			self.setControlOptions(i, ['var1', 'sin', 'ещё опции','и ещё вот'])
	
	def get_elapsed_time(self):
		return time.time() - self._time_start
	
	def getSensor(self, index):
		return self._program.getSensor(index).get_value()

	def getControlOption(self, index):
		return self._program.getSensorControlOption(index)
	
	def setControlOptions(self, index, options):
		self._program.setSensorControlOptions(index, options)
		
	
	def setSensor(self, index, value):
#		print(f'oat: {value}')
		self._program.setSensor(index, value)

	def compute_temperature(self, index):
		value  = self.getSensor(index)
		option = self.getControlOption(index)
		
		if option == 'sin':
			pi = 3.14
			ds = math.cos(self.get_elapsed_time()/100.0 + pi/2)
			value = value + ds * 0.5
		if option == 'var1':
			inc = 0.01
			value = 6
		return value

	def run(self):
		for i in range(0,VIRTUAL_SENSORS_MAX_NUM):
			self.setSensor(i, self.compute_temperature(i))


import math
import time


BROADCAST_ID = 0

from functions.limit import limit

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.get_preset()
		self._time_start    = time.time()
		self._control    = control
		self._sourceList = self._program.getCascadeManagerSourceList()
		
		self.set_temperature(30)

	def get_temperature(self):
		return self._program.get_input_channel('temperature').get_value()

	def set_temperature(self, value):
#		print(f'cascade: {value}')
		self._program.get_input_channel('temperature').set_value(value)

	def get_elapsed_time(self):
		return time.time() - self._time_start

	def get_consumer_power(self):
		consumersPower = self._control.get_consumer_power(self._program.get_id())
		return consumersPower

	def get_power(self):
		sourceList     = self._control.getSourceList()

		power = 0
		for source in sourceList:
			if source._program.get_id() in self._sourceList:
				power = power + source.get_power()

		return power

	def get_cooldown_power(self):
		return 1

	def get_total_power(self):
		return self.get_power() - self.get_consumer_power() - self.get_cooldown_power()

	def compute_temperature(self):
		temp = self._control._collector.getDirectTemperature()
		
		temp = limit(-30, temp, 100)

		return temp

	def get_flow(self):
		return 0
		
#		sourceList     = self._control.getSourceList()
#		selfSourceList = self._program.get_preset().getSettings().getSourceList()

#		flow = 0
#		for source in sourceList:
#			if source._program.get_id() in selfSourceList:
#				flow = flow + source.get_flow()

#		return flow
	
	def run(self):
		self.set_temperature(self.compute_temperature())

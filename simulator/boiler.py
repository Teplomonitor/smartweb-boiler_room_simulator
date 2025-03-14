
import math
import time
from smartnet.units import TEMPERATURE as TEMPERATURE
from simulator.sensorReport import reportSensorValue as reportSensorValue

BROADCAST_ID = 0

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, thread_name, thread_ID, program, canbus, control):
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._program    = program
		self._preset     = self._program.getPreset()
		self._time_start    = time.time()
		self._control    = control
		
		self._inputId = {
			'temperature'         : 0,
			'backwardTemperature' : 1,
			'outsideRequest'      : 2,
			'error'               : 3,
		}

		self._outputId = {
			'pump'                : 0,
			'burner1'             : 1,
			'burner2'             : 2,
			'power'               : 3,
			'temperature'         : 4,
			'backwardTemperature' : 5,
		}

		self.setTemperature(30)

	def getTemperature(self):
		return self._program.getInput(self._inputId['temperature']).getValue()

	def setTemperature(self, value):
		print(f'boiler: {value}')
		self._program.getInput(self._inputId['temperature']).setValue(value)

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getConsumersPower(self):
		programList = self._control.getConsumerList()
		consumerList = []
		for program in programList:
			sourceList = program._program.getPreset().getSettings().getSourceList()
			if ((self._program.getId() in sourceList) or
				(BROADCAST_ID in sourceList) ):
				consumerList.append(program)

		consumerPower = 0
		for consumer in consumerList:
			consumerPower = consumerPower + consumer.getPower()

		return consumerPower

	def temperatureInputIsMapped(self):
		temp = self._program.getInput(self._inputId['temperature'])
		mapping = temp.getMapping()
		if mapping is None:
			return False

		if mapping.getChannelType() == 'CHANNEL_UNDEFINED':
			return False

		return True


	def getStageState(self):
		stage = self._program.getOutput(self._outputId['burner1'])
		if stage.getMapping() is None:
			return 1

		if stage.getValue():
			return 1

		return 0

	def getMaxPower(self):
		return self._preset.getPower()

	def getPower(self):
		if self.getStageState():
			return self.getMaxPower()
		else:
			return 0

	def getCoolDownPower(self):
		return -1

	def getTotalPower(self):
		return self.getPower() + self.getConsumersPower() + self.getCoolDownPower()

	def computeTemperature(self):
		temp = self.getTemperature()
		temp = temp + self.getTotalPower() * 0.1

		temp = limit(-30, temp, 120)

		return temp

	def run(self):
		if self.temperatureInputIsMapped():
			self.setTemperature(self.computeTemperature())
			

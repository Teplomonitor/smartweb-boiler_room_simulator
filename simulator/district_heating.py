
import math
import time

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
			'supply_direct_temp'   : 0,
			'supply_backward_temp' : 1,
			'direct_temp'          : 2,
			'backward_temp'        : 3,
			'thermal_output'       : 4,
			'volume_flow'          : 5,
			'outside_request'      : 6,
		}

		self._outputId = {
			'supply_pump'         : 0,
			'circulation_pump'    : 1,
			'valve'               : 2,
			'analog_valve'        : 3,
		}

		self._tMax = 75
		self._tMin = 20
		self.setSupplyDirectTemperature(30)
		self.setSupplyBackwardTemperature(30)
		self.setDirectTemperature(30)
		self.setBackwardTemperature(30)
		self.setThermalOutputSensor(0)
		self.setVolumeFlowSensor(0)
		self.setOutsideRequestSensor(0)

	def getSupplyDirectTemperature(self):
		return self._program.getInput(self._inputId['supply_direct_temp']).getValue()

	def setSupplyDirectTemperature(self, value):
		self._program.getInput(self._inputId['supply_direct_temp']).setValue(value)

	def getSupplyBackwardTemperature(self):
		return self._program.getInput(self._inputId['supply_backward_temp']).getValue()

	def setSupplyBackwardTemperature(self, value):
		self._program.getInput(self._inputId['supply_backward_temp']).setValue(value)

	def getDirectTemperature(self):
		return self._program.getInput(self._inputId['direct_temp']).getValue()

	def setDirectTemperature(self, value):
		self._program.getInput(self._inputId['direct_temp']).setValue(value)

	def getBackwardTemperature(self):
		return self._program.getInput(self._inputId['backward_temp']).getValue()

	def setBackwardTemperature(self, value):
		self._program.getInput(self._inputId['backward_temp']).setValue(value)

	def getThermalOutputSensor(self):
		return self._program.getInput(self._inputId['thermal_output']).getValue()

	def setThermalOutputSensor(self, value):
		self._program.getInput(self._inputId['thermal_output']).setValue(value)

	def getVolumeFlowSensor(self):
		return self._program.getInput(self._inputId['volume_flow']).getValue()

	def setVolumeFlowSensor(self, value):
		self._program.getInput(self._inputId['volume_flow']).setValue(value)

	def getOutsideRequestSensor(self):
		return self._program.getInput(self._inputId['outside_request']).getValue()

	def setOutsideRequestSensor(self, value):
		self._program.getInput(self._inputId['outside_request']).setValue(value)

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
			Pmax = self.getMaxPower()
			Pmin = Pmax*0.5
			dt = self._tMax - self.getTemperature() 
			P = Pmin + (Pmax - Pmin) * dt/self._tMax
			return P
		else:
			return 0

	def getCoolDownPower(self):
		dt = self.getTemperature() - self._tMin
		return -1 * dt/self._tMax

	def getTotalPower(self):
		return self.getPower() + self.getConsumersPower() + self.getCoolDownPower()

	def computeTemperature(self):
		temp = self.getTemperature()
		temp = temp + self.getTotalPower() * 0.1

		temp = limit(self._tMin, temp, self._tMax)

		print(f'b{self._program.getId()} t = {temp}')
		
		return temp

	def run(self):
		self.setTemperature(self.computeTemperature())


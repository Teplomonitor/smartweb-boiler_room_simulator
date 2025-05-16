
import math
import time

BROADCAST_ID = 0

# https://proteplo.org/blog/teplovoy-raschet-teploobmennika
# Q = G*c*(T2-T1)
G = 500 #kg/h
c = 4200 # Joule/kg*C
Gc = G*c/1000/3.6 # kWatt


def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, program_config, control):
		self._program    = program_config
		self._preset     = self._program.getPreset()
		self._time_start    = time.time()
		self._control    = control
		
		self._district_heating_scenario = 'default'
		
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
		self._district_temperature = 65
		
		self.setSupplyDirectTemperature(60)
		self.setSupplyBackwardTemperature(50)
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

	def getTemperature(self):
		return self.getDirectTemperature()

	def getElapsedTime(self):
		return time.time() - self._time_start

	def getCascadePower(self):
		programList = self._control.getCascadeList()
		consumerList = []
		programId = self._program.getId()
		for program in programList:
			sourceList = program._program.getPreset().getSettings().getSourceList()
			if ((programId in sourceList) or
				(BROADCAST_ID in sourceList) ):
				consumerList.append(program)

		consumerPower = 0
		for consumer in consumerList:
			consumerPower = consumerPower + (consumer.getPower() - self.getPower()) # exclude own district heating power

		return consumerPower
	
	def getConsumersPower(self):
		consumersPower = self._control.getConsumersPower(self._program.getId())
		cascadePower = self.getCascadePower()
		return consumersPower + cascadePower


	def getPumpState(self, pumpId):
		pump = self._program.getOutput(self._outputId[pumpId])
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0
	
	def getSupplyPumpState(self):
		return self.getPumpState('supply_pump')
	
	def getValveState(self):
		valve        = self._program.getOutput(self._outputId['valve'])
		analog_valve = self._program.getOutput(self._outputId['analog_valve'])
		
		if (valve.getMapping() is None) and (analog_valve.getMapping() is None ):
			return 1

		valve = analog_valve.getValue()
		if valve is None:
			return 1
		# TODO: add binary valve use case
		return valve / 254
	
	def getCirculationPumpState(self):
		return self.getPumpState('circulation_pump')

	def getMaxPower(self):
		return self._preset.getPower()

	def getPower(self):
		if self.supplyFlowIsStopped():
			Q = 0
		else:
			t1 = self.getSupplyDirectTemperature()
			t2 = self.getSupplyBackwardTemperature()
			Q = Gc * (t1 - t2)
			
		print(f'District heating power {Q}')
		return Q

	def tempSlowCooling(self, temp):
		alpha = 0.1
		beta  = 1 - alpha
		roomTemp = 24
		temp = temp*beta + roomTemp*alpha
		temp = limit(20, temp, 80)
		
		return temp
		
	def supplyFlowIsStopped(self):
		return (self.getSupplyPumpState() == 0) or (self.getValveState() == 0)
	
	def secondaryFlowIsStopped(self):
		return self.getCirculationPumpState() == 0
	
	def computeSupplyDirectTemperature(self):
		temp = self.getSupplyDirectTemperature()
		if self.supplyFlowIsStopped():
			temp = self.tempSlowCooling(temp)
			return temp
		
		if self._district_heating_scenario == 'default':
			return 60

		return 50
	
	def computeSupplyBackwardTemperature(self):
		temp = self.getSupplyBackwardTemperature()
		if self.supplyFlowIsStopped():
			temp = self.tempSlowCooling(temp)
			return temp
		
		supplyDirectTemp = self.getSupplyDirectTemperature()
		backwardTemp     = self.getBackwardTemperature()

		valve = self.getValveState()

		supplyBackwardTemp = backwardTemp + valve*(supplyDirectTemp - backwardTemp)
		
		return supplyBackwardTemp

	def computeDirectTemperature(self):
		temp = self.getDirectTemperature()
		if self.secondaryFlowIsStopped():
			temp = self.tempSlowCooling(temp)
			return temp
		
		valve = self.getValveState()
		supplyDirectTemp = self.getSupplyDirectTemperature()
		backwardTemp     = self.getBackwardTemperature()
		
		directTemp = backwardTemp + valve*(supplyDirectTemp - backwardTemp)
		
		return directTemp
	
	def computeBackwardTemperature(self):
		return self._control._collector.getDirectTemperature()
		
	def run(self):
		self.setSupplyDirectTemperature  (self.computeSupplyDirectTemperature())
		self.setSupplyBackwardTemperature(self.computeSupplyBackwardTemperature())
		self.setDirectTemperature        (self.computeDirectTemperature())
		self.setBackwardTemperature      (self.computeBackwardTemperature())


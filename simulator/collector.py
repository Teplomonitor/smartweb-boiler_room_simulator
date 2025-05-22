



def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, control):
		self._supply_direct_temperature   = 40
		self._supply_backward_temperature = 40
		
		self._direct_temperature   = 40
		self._backward_temperature = 40
		
		self._control = control
		self._generatorList = []
		self._consumerList = self._control.getConsumerList()
		
		sourceList   = self._control.getSourceList()
		
		for source in sourceList:
			if source._program.getType() == 'CASCADE_MANAGER':
				#cascade do not produce temperature itself, exclude it
				pass
			else:
				self._generatorList.append(source)
		
	# temperature given by boilers
	def getSupplyDirectTemperature(self):
		return self._supply_direct_temperature
	
	def setSupplyDirectTemperature(self, temp):
		self._supply_direct_temperature = temp
	
	# temperature return to boilers
	def getSupplyBackwardTemperature(self):
		return self._supply_backward_temperature
	
	def setSupplyBackwardTemperature(self, temp):
		self._supply_backward_temperature = temp
	
	# temperature given to consumers
	def getDirectTemperature(self):
		return self._direct_temperature
	
	def setDirectTemperature(self, temp):
		self._direct_temperature = temp
	
	# temperature returned from consumers
	def getBackwardTemperature(self):
		return self._backward_temperature
	
	def setBackwardTemperature(self, temp):
		self._backward_temperature = temp
	
	def computeSupplyDirectTemperature(self):
		temp = self.getSupplyDirectTemperature()
		
		sumTemp = 0
		i = 0
		
		for generator in self._generatorList:
			if generator.getFlow() != 0:
				sumTemp = sumTemp + generator.getTemperature()
				i = i + 1
		
		if i > 0:
			avrTemp = sumTemp / i
		else:
			avrTemp = self.getSupplyBackwardTemperature()
			
		alpha = 0.1
		beta  = 1 - alpha
		
		temp = temp*beta + avrTemp*alpha
		
		return temp
		
	def computeSupplyBackwardTemperature(self):
		direct   = self.getSupplyDirectTemperature()
		backward = self.getBackwardTemperature()
		
		activeConsumersNum  = 0
		activeGeneratorsNum = 0
		
		consumerFlow = 0
		for consumer in self._consumerList:
			if consumer.getPower() != 0:
				activeConsumersNum = activeConsumersNum + 1
				consumerFlow = consumerFlow + 1
				
		generatorFlow = 0 
		for generator in self._generatorList:
			if generator.getFlow() != 0:
				activeGeneratorsNum = activeGeneratorsNum + 1
				generatorFlow = generatorFlow + generator.getFlow()
		
		if activeConsumersNum == 0:
			return direct
		
		if activeGeneratorsNum == 0:
			return backward
		
		totalFlow = consumerFlow + generatorFlow
		
		alpha = generatorFlow / totalFlow
		beta  = consumerFlow  / totalFlow
		
		backward = self.getBackwardTemperature()
		
		avrTemp = direct * alpha + backward * beta
		
		return avrTemp
		
	def computeDirectTemperature(self):
		return self.getSupplyDirectTemperature() -1 # assume we losing a bit
		
	def computeBackwardTemperature(self):
		temp = self.getBackwardTemperature()
		
		sumTemp = 0
		i = 0
		
		for consumer in self._consumerList:
			if consumer.getPower() != 0:
				sumTemp = sumTemp + consumer.getBackwardTemperature()
				i = i + 1
		
		if i > 0:
			avrTemp = sumTemp / i
		else:
			avrTemp = self.getDirectTemperature()
		
		alpha = 0.1
		beta  = 1 - alpha
		
		temp = temp*beta + avrTemp*alpha
		
		return temp
	
	def run(self):
		self.setSupplyDirectTemperature  (self.computeSupplyDirectTemperature  ())
		self.setDirectTemperature        (self.computeDirectTemperature  ())
		self.setBackwardTemperature      (self.computeBackwardTemperature())
		self.setSupplyBackwardTemperature(self.computeSupplyBackwardTemperature())
		
		t1 = self.getSupplyDirectTemperature()
		t2 = self.getSupplyBackwardTemperature()
		t3 = self.getDirectTemperature()
		t4 = self.getBackwardTemperature()
		
		print(f'collector: {t1:.2f} {t2:.2f} {t3:.2f} {t4:.2f}')
		
	

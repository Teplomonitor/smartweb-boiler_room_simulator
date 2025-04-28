



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
		
		sourceList = self._control.getSourceList()
		
		for source in sourceList:
			if source._program.getType() == 'CASCADE_MANAGER':
				#cascade do not produce temperature itself
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
		
		for generator in self._generatorsList:
			if generator.getPower() != 0:
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
		temp = self.getSupplyDirectTemperature()
		
		
		
		
	def run(self):
		self.setSupplyDirectTemperature  (self.computeSupplyDirectTemperature  ())
		self.setSupplyBackwardTemperature(self.computeSupplyBackwardTemperature())
		
	

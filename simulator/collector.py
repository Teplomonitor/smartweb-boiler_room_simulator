

class Simulator(object):
	def __init__(self, control):
		self._supply_direct_temperature   = 40
		self._supply_backward_temperature = 40
		
		self._direct_temperature   = 40
		self._backward_temperature = 40
		
		self._control = control
		self._generatorList = []
		self._consumerList = self._control.getConsumerList()
		
		self._consumerFlow  = 0
		self._generatorFlow = 0
		
		sourceList   = self._control.getSourceList()
		
		for source in sourceList:
			if source._program.get_type() == 'CASCADE_MANAGER':
				#cascade do not produce temperature itself, exclude it
				pass
			else:
				self._generatorList.append(source)
		
	# temperature given by boilers
	def get_supply_direct_temperature(self):
		return self._supply_direct_temperature
	
	def set_supply_direct_temperature(self, temp):
		self._supply_direct_temperature = temp
	
	# temperature return to boilers
	def get_supply_backward_temperature(self):
		return self._supply_backward_temperature
	
	def get_supply_backward_temperature(self, temp):
		self._supply_backward_temperature = temp
	
	# temperature given to consumers
	def get_direct_temperature(self):
		return self._direct_temperature
	
	def set_direct_temperature(self, temp):
		self._direct_temperature = temp
	
	# temperature returned from consumers
	def get_backward_temperature(self):
		return self._backward_temperature
	
	def set_backward_temperature(self, temp):
		self._backward_temperature = temp
	
	def compute_supply_direct_temperature(self):
		sumTemp = 0
		i = 0
		
		for generator in self._generatorList:
			if generator.get_flow() != 0:
				sumTemp = sumTemp + generator.get_temperature()
				i = i + 1
		
		if i > 0:
			avrTemp = sumTemp / i
		else:
			avrTemp = self.get_supply_backward_temperature()
			
		temp = avrTemp
		
		return temp
		
	def compute_supply_backward_temperature(self):
		direct   = self.get_supply_direct_temperature()
		backward = self.get_backward_temperature()
		
		activeConsumersNum  = 0
		activeGeneratorsNum = 0
		
		consumerFlow = 0
		for consumer in self._consumerList:
			if consumer.get_power() != 0:
				activeConsumersNum = activeConsumersNum + 1
				consumerFlow = consumerFlow + consumer.get_flow()
				
		self._consumerFlow = consumerFlow
		
		generatorFlow = 0 
		for generator in self._generatorList:
			if generator.get_flow() != 0:
				activeGeneratorsNum = activeGeneratorsNum + 1
				generatorFlow = generatorFlow + generator.get_flow()
		
		self._generatorFlow = generatorFlow
		
		if activeConsumersNum == 0:
			return direct
		
		if activeGeneratorsNum == 0:
			return backward
		
		totalFlow = consumerFlow + generatorFlow
		
		alpha = generatorFlow / totalFlow
		beta  = consumerFlow  / totalFlow
		
		backward = self.get_backward_temperature()
		
		avrTemp = direct * alpha + backward * beta
		
		return avrTemp
		
	def compute_direct_temperature(self):
		return self.get_supply_direct_temperature() -1 # assume we losing a bit
		
	def compute_backward_temperature(self):
		sumTemp = 0
		i = 0
		
		consumerFlow = 0
		for consumer in self._consumerList:
			if consumer.get_power() != 0:
				consumerFlow = consumerFlow + consumer.get_flow()
				i = i + 1
		
		for consumer in self._consumerList:
			if consumer.get_power() != 0:
				sumTemp = sumTemp + consumer.get_backward_temperature() * consumer.get_flow() / consumerFlow
				i = i + 1
		
		if i > 0:
			avrTemp = sumTemp
		else:
			avrTemp = self.get_direct_temperature()
		
		return avrTemp
	
	def run(self):
		self.set_supply_direct_temperature  (self.compute_supply_direct_temperature  ())
		self.set_direct_temperature        (self.compute_direct_temperature  ())
		self.set_backward_temperature      (self.compute_backward_temperature())
		self.get_supply_backward_temperature(self.compute_supply_backward_temperature())
		
		t1 = self.get_supply_direct_temperature()
		t2 = self.get_supply_backward_temperature()
		t3 = self.get_direct_temperature()
		t4 = self.get_backward_temperature()
		
		f1 = self._consumerFlow
		f2 = self._generatorFlow
		
#		print(f'collector: {t1:.2f} {t2:.2f} {t3:.2f} {t4:.2f} flow {f1:.2f} {f2:.2f} ')
		
	

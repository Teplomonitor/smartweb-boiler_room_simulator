
import smartnet.constants as snc

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
			if source._program.get_type() == snc.ProgramType.CASCADE_MANAGER:
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
	
	def set_supply_backward_temperature(self, temp):
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
	
	# flow given to consumers
	def get_consumer_flow(self):
		return self._consumerFlow
	
	# flow on the boilers side
	def get_generator_flow(self):
		return self._generatorFlow
	
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
		
		if self._consumerFlow == 0:
			return direct
		
		if self._generatorFlow == 0:
			return backward
		
		totalFlow = self._consumerFlow + self._generatorFlow
		
		alpha = self._generatorFlow / totalFlow
		beta  = self._consumerFlow  / totalFlow
		
		backward = self.get_backward_temperature()
		
		avrTemp = direct * alpha + backward * beta
		
		return avrTemp
		
	def compute_direct_temperature(self):
		return self.get_supply_direct_temperature() -1 # assume we losing a bit
		
	def compute_consumer_flow(self):
		consumerFlow = 0
		
		for consumer in self._consumerList:
			if consumer.get_power() != 0:
				consumerFlow = consumerFlow + consumer.get_flow()
		
		return consumerFlow
	
	def compute_generator_flow(self):
		generatorFlow = 0
		
		for generator in self._generatorList:
			if generator.get_flow() != 0:
				generatorFlow = generatorFlow + generator.get_flow()
		
		return generatorFlow
	
	def compute_backward_temperature(self):
		sumTemp = 0
		i = 0
		
		for consumer in self._consumerList:
			if consumer.get_power() != 0:
				sumTemp = sumTemp + consumer.get_backward_temperature() * consumer.get_flow() / self._consumerFlow
				i = i + 1
		
		if i > 0:
			avrTemp = sumTemp
		else:
			avrTemp = self.get_direct_temperature()
		
		return avrTemp
	
	def run(self):
		self._consumerFlow  = self.compute_consumer_flow()
		self._generatorFlow = self.compute_generator_flow()
		
		self.set_supply_direct_temperature  (self.compute_supply_direct_temperature  ())
		self.set_direct_temperature         (self.compute_direct_temperature  ())
		self.set_backward_temperature       (self.compute_backward_temperature())
		self.set_supply_backward_temperature(self.compute_supply_backward_temperature())
		
	

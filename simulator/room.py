
from functions.limit import limit

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.get_preset()
		self._control    = control

		self.set_temperature(20)
		
		self._roomSourceList = self._program.getRoomTemperatureSourceList()


	def getOat(self):
		oat = self._control.getOat()
		if oat is None:
			return 0
			
		return oat.get_temperature()

	def get_temperature(self):
		return self._program.get_temperature().get_value()

	def set_temperature(self, value):
		self._program.set_temperature(value)

	def get_max_power(self):
		return self._program.get_max_power()
	
	def getSourceTemperature(self, sourceId):
		sourceList       = self._control.getHeatingCircuitList()
		
#		print(f'source list {roomSourceList}')
		for source in sourceList:
			programId = source._program.get_id()
#			print(f'source id = {programId}')
			if programId == self._roomSourceList[sourceId]:
#				print(f'source {sourceId} found')
				if source.get_power():
					return source.get_temperature()

		return self.get_temperature()
	
	def getSourcePower(self, sourceId):
		sourceList       = self._control.getHeatingCircuitList()
		
		for source in sourceList:
			if source._program.get_id() == self._roomSourceList[sourceId]:
				return source.get_power()

		return 0
	
	def getFloorPower(self):
		return self.getSourcePower(0)
	
	def getRadiatorPower(self):
		return self.getSourcePower(1)
	
	def getAdditionalSourcePower(self):
		return self.getSourcePower(2)

	def getFloorTemperature(self):
		return self.getSourceTemperature(0)
	
	def getRadiatorTemperature(self):
		return self.getSourceTemperature(1)
	
	def getAdditionalSourceTemperature(self):
		return self.getSourceTemperature(2)

	def getHeating(self):
		floorTemp    = self.getFloorTemperature()
		radiatorTemp = self.getRadiatorTemperature()
		wallTemp     = self.getAdditionalSourceTemperature()
		
		
		temp  = self.get_temperature()
		
#		print(f'floor={floorTemp} rad={radiatorTemp} wall={wallTemp} self={temp}')
		
		dTrad   = radiatorTemp - temp
		dTfloor = floorTemp    - temp
		dTwall  = wallTemp     - temp
		
		return dTfloor*0.15 + dTrad*0.1 + dTwall*0.1

	def getCooling(self):
		temp  = self.get_temperature()
		oat   = self.getOat()
		
		dT = oat - temp
		
		return dT*0.1
		

	def compute_temperature(self):
		temp = self.get_temperature()
		temp = temp + (self.getHeating() + self.getCooling())*0.0005
		temp = limit(-10, temp, 50)

		return temp

	def run(self):
		self.set_temperature(self.compute_temperature())

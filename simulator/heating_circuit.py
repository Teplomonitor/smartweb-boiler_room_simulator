
from functions.limit import limit

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.get_preset()
		self._control    = control
		
		self._roomTemp = 24
		self.set_temperature(20)
		self.setBackwardTemperature(20)
		self.setBackwardTemperature2(20)

	def getOat(self):
		oat = self._control.getOat()
		if oat is None:
			return 0
			
		return oat.get_temperature()
	
	def getRoomTemp(self):
		return self._roomTemp

	def get_temperature(self):
		return self._program.get_input_channel('temperature').getValue()

	def set_temperature(self, value):
		self._program.get_input_channel('temperature').setValue(value)

	def getBackwardTemperature(self):
		return self._supplyBackwardTemperature

	def setBackwardTemperature(self, value):
		self._supplyBackwardTemperature = value

	def getBackwardTemperature2(self):
		return self._program.get_input_channel('backwardTemperature').getValue()

	def setBackwardTemperature2(self, value):
		self._program.get_input_channel('backwardTemperature').setValue(value)

	def get_max_flow_rate(self):
		return self._program.get_max_flow_rate()
	
	def getPumpState(self):
		pump = self._program.get_output_channel('pump')
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0

	def getValveState(self):
		valve = self._program.get_output_channel('analogValve')
		if valve.getMapping() is None:
			return 1

		valve = valve.getValue()
		if valve is None:
			return 1
		return valve / 254

	def get_max_power(self):
		return self._program.get_max_power()

	def getPower(self):
		if self.getPumpState() == 0:
			return 0

		return self.getValveState()*self.get_max_power()

	def getFlow(self):
		rate = self.get_max_flow_rate() / 1000 # cube per hour
		return self.getPumpState() * self.getValveState() * rate
	
	def getSourceTemperature(self):
		return self._control._collector.getDirectTemperature()

	def computeTemperature(self):
		tempBackward = self.getBackwardTemperature2()
		temp        = self.get_temperature()
		roomTemp    = self.getRoomTemp()

		if self.getPumpState() == 0:
			alpha = 0.01
			beta  = 1 - alpha
			return temp*beta + roomTemp*alpha

		sourceTemp = self.getSourceTemperature()

		valve = self.getValveState()
		
		temp = tempBackward + (sourceTemp - tempBackward) * valve

		temp = limit(-30, temp, 120)

		return temp
	
	def computeBackwardTemperature2(self):
		temp       = self.getBackwardTemperature2()
		roomTemp   = self.getRoomTemp()
		oat        = self.getOat()
		
		avrRoomTemp = (roomTemp*1.5 + oat*0.5)/2
		
		if self.getPumpState() == 0:
			alpha = 0.01
			beta  = 1 - alpha
			return temp*beta + avrRoomTemp*alpha
		
		tempDirect = self.get_temperature()
		
		cw = 4200 # теплоемкость воды
		qhouse = self.get_max_flow_rate() / 3600 # расход кг/сек в доме постоянный.
		cwq = qhouse*cw # так короче
		btermo=1200 # теплоотдача батарей НЕ трогать
		troom = roomTemp
		tinhouse = tempDirect
		
		t_rethouse = ((cwq - btermo/2)*tinhouse + btermo * troom)/(cwq+btermo/2) # обратка из дома
		
		return t_rethouse
	
	def computeBackwardTemperature(self):
		temp = self.getBackwardTemperature2()
		
		valve = self.getValveState()
		sourceTemp = self.getSourceTemperature()
		
		temp = temp * valve + sourceTemp * (1 - valve)

		return temp

	def run(self):
		self.set_temperature         (self.computeTemperature())
		self.setBackwardTemperature2(self.computeBackwardTemperature2())
		self.setBackwardTemperature (self.computeBackwardTemperature ())

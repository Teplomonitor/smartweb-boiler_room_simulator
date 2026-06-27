
from functions.limit import limit

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.get_preset()
		self._control    = control
		
		self._roomTemp = 24
		self.set_temperature(20)
		self.set_backward_temperature(20)
		self.set_backward_temperature2(20)

	def getOat(self):
		oat = self._control.getOat()
		if oat is None:
			return 0
			
		return oat.get_temperature()
	
	def getRoomTemp(self):
		return self._roomTemp

	def get_temperature(self):
		return self._program.get_input_channel('temperature').get_value()

	def set_temperature(self, value):
		self._program.get_input_channel('temperature').set_value(value)

	def get_backward_temperature(self):
		return self._supplyBackwardTemperature

	def set_backward_temperature(self, value):
		self._supplyBackwardTemperature = value

	def get_backward_temperature2(self):
		return self._program.get_input_channel('backwardTemperature').get_value()

	def set_backward_temperature2(self, value):
		self._program.get_input_channel('backwardTemperature').set_value(value)

	def get_max_flow_rate(self):
		return self._program.get_max_flow_rate()
	
	def get_pump_state(self):
		pump = self._program.get_output_channel('pump')
		if pump.get_mapping() is None:
			return 1

		if pump.get_value():
			return 1

		return 0

	def getValveState(self):
		valve = self._program.get_output_channel('analogValve')
		if valve.get_mapping() is None:
			return 1

		valve = valve.get_value()
		if valve is None:
			return 1
		return valve / 254

	def get_max_power(self):
		return self._program.get_max_power()

	def get_power(self):
		if self.get_pump_state() == 0:
			return 0

		return self.getValveState()*self.get_max_power()

	def get_flow(self):
		rate = self.get_max_flow_rate() / 1000 # cube per hour
		return self.get_pump_state() * self.getValveState() * rate
	
	def getSourceTemperature(self):
		return self._control._collector.get_direct_temperature()

	def compute_temperature(self):
		tempBackward = self.get_backward_temperature2()
		temp        = self.get_temperature()
		roomTemp    = self.getRoomTemp()

		if self.get_pump_state() == 0:
			alpha = 0.01
			beta  = 1 - alpha
			return temp*beta + roomTemp*alpha

		sourceTemp = self.getSourceTemperature()

		valve = self.getValveState()
		
		temp = tempBackward + (sourceTemp - tempBackward) * valve

		temp = limit(-30, temp, 120)

		return temp
	
	def compute_backward_temperature2(self):
		temp       = self.get_backward_temperature2()
		roomTemp   = self.getRoomTemp()
		oat        = self.getOat()
		
		avrRoomTemp = (roomTemp*1.5 + oat*0.5)/2
		
		if self.get_pump_state() == 0:
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
	
	def compute_backward_temperature(self):
		temp = self.get_backward_temperature2()
		
		valve = self.getValveState()
		sourceTemp = self.getSourceTemperature()
		
		temp = temp * valve + sourceTemp * (1 - valve)

		return temp

	def run(self):
		self.set_temperature         (self.compute_temperature())
		self.set_backward_temperature2(self.compute_backward_temperature2())
		self.set_backward_temperature (self.compute_backward_temperature ())

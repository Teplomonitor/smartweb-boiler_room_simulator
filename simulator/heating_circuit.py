

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, program, control):
		self._program    = program
		self._preset     = self._program.getPreset()
		self._control    = control
		
		self._outputId = {
			'analogValve'     : 0,
			'tptValveOpen'    : 1,
			'tptValveClose'   : 2,
			'pump'            : 3,
			'thermomotor'     : 4,
			'heatchangePump'  : 5,
			'analogPump'      : 6,
		}

		self._inputId = {
			'temperature'         : 0,
			'thermostat'          : 1,
			'outsideRequest'      : 2,
			'pumpControl'         : 3,
			'backwardTemperature' : 4,
		}
		
		self._roomTemp = 24
		self.setTemperature(20)
		self.setBackwardTemperature(20)
		self.setBackwardTemperature2(20)

	def getOat(self):
		oat = self._control.getOat()
		if oat is None:
			oat = 0
			
		return oat.getTemperature()
	
	def getRoomTemp(self):
		return self._roomTemp

	def getTemperature(self):
		return self._program.getInput(self._inputId['temperature']).getValue()

	def setTemperature(self, value):
		self._program.getInput(self._inputId['temperature']).setValue(value)

	def getBackwardTemperature(self):
		return self._supplyBackwardTemperature

	def setBackwardTemperature(self, value):
		self._supplyBackwardTemperature = value

	def getBackwardTemperature2(self):
		return self._program.getInput(self._inputId['backwardTemperature']).getValue()

	def setBackwardTemperature2(self, value):
		self._program.getInput(self._inputId['backwardTemperature']).setValue(value)

	def getPumpState(self):
		pump = self._program.getOutput(self._outputId['pump'])
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0

	def getValveState(self):
		valve = self._program.getOutput(self._outputId['analogValve'])
		if valve.getMapping() is None:
			return 1

		valve = valve.getValue()
		if valve is None:
			return 1
		return valve / 254

	def getMaxPower(self):
		return self._preset.getPower()

	def getPower(self):
		if self.getPumpState() == 0:
			return 0

		return self.getValveState()*self.getMaxPower()

	def getFlow(self):
		return self.getPumpState() * self.getValveState() * 1 # cube per hour
	
	def getSourceTemperature(self):
		return self._control._collector.getDirectTemperature()

	def computeTemperature(self):
		tempBackward = self.getBackwardTemperature2()
		temp        = self.getTemperature()
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
		
		tempDirect = self.getTemperature()
		
		cw = 4200 # теплоемкость воды
		qhouse = 1/3.6 # расход кг/сек в доме постоянный.
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
		self.setTemperature         (self.computeTemperature())
		self.setBackwardTemperature2(self.computeBackwardTemperature2())
		self.setBackwardTemperature (self.computeBackwardTemperature ())

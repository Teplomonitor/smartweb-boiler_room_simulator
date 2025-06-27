

import math
import time

BROADCAST_ID = 0

# https://proteplo.org/blog/teplovoy-raschet-teploobmennika
# начальные условия

cw = 4200 # теплоемкость воды  Joule/kg*C

ato = 3000 # теплопередача ТО тоже не трогать

sqwear=1 # Площадь ТО в кв.м.-----------------------
atos=ato * sqwear
tau=1 # шаг по времени сек

G = 500 #kg/h
Gc = G*cw/3600/1000 # kWatt

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

class Simulator(object):
	def __init__(self, program_config, control):
		self._program    = program_config
		self._preset     = self._program.getPreset()
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
		self._qtown = 0 # расход из города при данном угле сервака
		self._init = True
		
		self.setSupplyDirectTemperature(60)
		self.setSupplyBackwardTemperature(50)
		self.setDirectTemperature(30)
		self.setBackwardTemperature(30)
		self.setThermalOutputSensor(0)
		self.setVolumeFlowSensor(0)
		self.setOutsideRequestSensor(0)
		
		self.tintown    = self.getSupplyDirectTemperature()
		self.t_rethouse = self.getBackwardTemperature()
		
		self.tinhouse   = self.getDirectTemperature()
		self.t_rettown  = self.getSupplyBackwardTemperature()
		
		self.qtown  = 0

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
			power = 0
		else:
			valve      = self.getValveState()
			t_rettown  = self.getSupplyBackwardTemperature()
			tintown    = self.getSupplyDirectTemperature()
			ugolserv   = valve
		
			qtown = qtown_max * ugolserv # расход из города при данном угле сервака
			power = qtown*cw*(tintown-t_rettown) # подсчет текущей мощности теплопередачи ватт
			
		Q = power /1000
#		print(f'District heating power {Q:.1f}')
		return Q

	def tempSlowCooling(self, temp):
		alpha = 0.001
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
			avrTemp = 70
			hour = 3600
			currentTime = time.time() % hour
			pi = 3.14
			offset = 2 * math.cos(2*pi * currentTime/hour)
			return avrTemp + offset

		return 85

	def computeBackwardTemperature(self):
		t_rethouse = self._control._collector.getSupplyBackwardTemperature()
		return t_rethouse
	
	def ddtf(self):
		d1 = self.tintown   - self.tinhouse 
		d2 = self.t_rettown - self.t_rethouse
		d_tmax=d1
		d_tmin=d2
		d = d_tmin/d_tmax
		if  d > 20: #!!!!!!!!!!!!!!!!!!!!!!!!!!!
			ddt = (d_tmax - d_tmin) / math.log( d_tmax/d_tmin )
		else :	
			ddt = (d_tmax + d_tmin)/2 
		return ddt
	
	def getMaxFlowRateHouse(self):
		return self._program.getMaxFlowRate1() / 3600 # расход кг/сек в доме постоянный.
	
	def getMaxFlowRateTown(self):
		return self._program.getMaxFlowRate2() / 3600 # расход кг/сек в городе постоянный.
	
	def findom(self):
		# подача и обратка дома
		if self.secondaryFlowIsStopped():
			self.tinhouse = self.tempSlowCooling(self.tinhouse)
			return self.tinhouse
		
		qhouse = self.getMaxFlowRateHouse()
		
		self.tinhouse = self.qtown*(self.tintown - self.t_rettown)/qhouse + self.t_rethouse
		return self.tinhouse
	
	def ft_rettown(self, ddt):
		# обратка в город
		if self.qtown == 0 or self.supplyFlowIsStopped():
			self.t_rettown = self.tempSlowCooling(self.t_rettown)
			return self.t_rettown
		
		self.t_rettown = self.tintown - atos*ddt/(cw*self.qtown)
		if self.t_rettown < self.t_rethouse:
			#print('!!!!!', t_rettown)
			self.t_rettown = self.t_rethouse
		return self.t_rettown
	
	def mainframe(self):
		j=0
		d_teta = 10
		ddt = self.ddtf() # температурный напор
		while j<20 and abs(d_teta) > 0.5 : # утрясаем температуры при изменении расхода
			
			ddt0=ddt
			self.findom()
			
			#ddtf()
			self.ft_rettown(ddt)
			
			#ddtf()
#			frettdom()
			
			ddt = self.ddtf()
			d_teta=ddt-ddt0
			
			#fenergy() # вроде нормально все с энергией - проверку можно выключить
			
			j = j + 1
			#print('j', j, 'd_teta %.2f.'% d_teta, ddt)	
		#print('i',i, 'энергия города', etown, ' дом ', ehouse,'----------------------') 
	def computeTemp(self):
		valve = self.getValveState()
		ugolserv = valve
		
		#workaround
#		if ugolserv > 1:
#			ugolserv = 1
			
		if self._init and ugolserv:
			self._init = False
			self.tinhouse  = self.tintown + (self.t_rethouse - self.tintown) * ugolserv
			self.t_rettown = self.tintown*ugolserv+self.tinhouse*(1-ugolserv)
		
		qtown_max = self.getMaxFlowRateTown()
		
		self.qtown = qtown_max * ugolserv * self.getSupplyPumpState()# расход из города при данном угле сервака

		self.mainframe()
		
		
		
	def getFlow(self):
		if self.getCirculationPumpState():
			return self.getMaxFlowRateHouse() / 1000 # cube per hour
		return 0
	
	def run(self):
		self.tintown    = self.computeSupplyDirectTemperature()
		self.t_rethouse = self.computeBackwardTemperature()
		
		self.computeTemp()
		
		self.setSupplyDirectTemperature  (self.tintown   )
		self.setBackwardTemperature      (self.t_rethouse)
		self.setDirectTemperature        (self.tinhouse  )
		self.setSupplyBackwardTemperature(self.t_rettown )


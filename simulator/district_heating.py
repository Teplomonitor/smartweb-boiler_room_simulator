

import math
import time

BROADCAST_ID = 0

# https://proteplo.org/blog/teplovoy-raschet-teploobmennika
# начальные условия

cw = 4200 # теплоемкость воды  Joule/kg*C
qhouse_chas = 3 # расход куб в час в отоплении
qhouse = qhouse_chas/3.6 # расход кг/сек в доме постоянный.

qtown_chas_max = 3 # мах расход куб в час из города
qtown_max = qtown_chas_max/3.6 # секундный из города

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
		alpha = 0.01
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
	
	def computeSupplyBackwardTemperature(self):
		t_rettown  = self.getSupplyBackwardTemperature()
		if self.supplyFlowIsStopped():
			t_rettown = self.tempSlowCooling(t_rettown)
			return t_rettown
		
		valve = self.getValveState()

		tintown    = self.getSupplyDirectTemperature()
		tinhouse   = self.getDirectTemperature()
		t_rethouse = self.getBackwardTemperature()
		ugolserv   = valve
		
		qtown = qtown_max * ugolserv # расход из города при данном угле сервака

		t_rettown = tintown-(ato * qtown/qtown_max)*((tintown+t_rettown)/2 - (tinhouse+t_rethouse)/2)/cw #обратка в город
		
		return t_rettown

	def computeDirectTemperature(self):
		tinhouse = self.getDirectTemperature()
		if self.secondaryFlowIsStopped():
			tinhouse = self.tempSlowCooling(tinhouse)
			return tinhouse
		
		valve = self.getValveState()
		ugolserv = valve
		
		qtown = qtown_max * ugolserv * self.getSupplyPumpState()# расход из города при данном угле сервака and active pump
		
		t_rethouse = self.getBackwardTemperature()
		t_rettown  = self.getSupplyBackwardTemperature()
		tintown    = self.getSupplyDirectTemperature()
		
		if self.getCirculationPumpState() == 0:
			return t_rethouse
			
		etown  = tau*qtown *cw*(tintown - t_rettown)
		ehouse = tau*qhouse*cw*(tinhouse-t_rethouse)

		d_tinhouse = (etown-ehouse)/(cw*tau*qhouse) #подача в дом - подсчет разности энергий

		tinhouse = tinhouse + d_tinhouse # подача в дом
		
		return tinhouse
	
	def computeBackwardTemperature(self):
		t_rethouse = self._control._collector.getSupplyBackwardTemperature()
		return t_rethouse
		
	def computeTemp(self):
		tintown    = self.getSupplyDirectTemperature()
		t_rethouse = self.getBackwardTemperature()
		
		tinhouse   = self.getDirectTemperature()
		t_rettown  = self.getSupplyBackwardTemperature()
		
		valve = self.getValveState()
		ugolserv = valve
		
#		if ugolserv > 0.9:
#			ugolserv = 0.9
			
		if self._init and ugolserv:
			self._init = False
			tinhouse = tintown + (t_rethouse - tintown) * ugolserv
			t_rettown = tintown*ugolserv+tinhouse*(1-ugolserv)
		
		qtown0 = self._qtown
		qtown = qtown_max * ugolserv * self.getSupplyPumpState()# расход из города при данном угле сервака
		d_qtown=qtown-qtown0
		
		self._qtown = qtown
		
		
		power1 = 0
		j=0
		d_trettown=10
		while j<50 and abs(d_trettown) >0.5: # приращение Т обратки в город меньше 0,5
		
			d_tmax = tintown + t_rettown
			d_tmin = tinhouse + t_rethouse
	
			# энергия которая передается через пластину
			d_power=atos*d_qtown*(d_tmax - d_tmin)/2
			
			if qtown == 0 or self.supplyFlowIsStopped():
				t_rettown = self.tempSlowCooling(t_rettown)
			else:
				d_trettown = (d_qtown*(tintown - t_rettown)-d_power/cw)/qtown # прирост Т обр город d_power - прирост энергии d_qtown - прирост расхода
				t_rettown = t_rettown + d_trettown
			
			# подача в дом 
			if self.secondaryFlowIsStopped():
				tinhouse = self.tempSlowCooling(tinhouse)
			else:
				etown=qtown*cw*(tintown - t_rettown)
				ehouse=qhouse*cw*(tinhouse-t_rethouse)
				d_tinhouse = (etown-ehouse)/(cw*qhouse) #подача в дом - подсчет разности энергий
				tinhouse = tinhouse+d_tinhouse

			power1 = cw * qtown * (tintown - t_rettown)
			j +=1
			
#		print('tinhouse %.2f.' % tinhouse, 'rethous %.2f.' % t_rethouse,'rettown %.2f.' % t_rettown,'power %.2f.'% power1 )
		
		self.setDirectTemperature        (tinhouse)
		self.setSupplyBackwardTemperature(t_rettown)
		
		
	def getFlow(self):
		if self.getCirculationPumpState():
			return 2 # cube per hour
		return 0
	
	def run(self):
		self.setSupplyDirectTemperature  (self.computeSupplyDirectTemperature())
		self.setBackwardTemperature      (self.computeBackwardTemperature())
		
#		self.setSupplyBackwardTemperature(self.computeSupplyBackwardTemperature())
#		self.setDirectTemperature        (self.computeDirectTemperature())
		
		self.computeTemp()
		
#		t1 = self.getSupplyDirectTemperature()
#		t2 = self.getSupplyBackwardTemperature()
#		t3 = self.getDirectTemperature()
#		t4 = self.getBackwardTemperature()
		
#		p  = self.getPower()
		
#		print(f'tinhouse = {t3:.2f} t_rethouse = {t4:.2f} tintown = {t1:.2f} t_rettown = {t2:.2f} power = {p:.2f}')


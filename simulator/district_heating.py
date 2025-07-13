

import math
import time
import numpy as np

BROADCAST_ID = 0

# https://proteplo.org/blog/teplovoy-raschet-teploobmennika
# начальные условия

cw = 4200 # теплоемкость воды  Joule/kg*C

G = 500 #kg/h
Gc = G*cw/3600/1000 # kWatt

square=1 # Площадь ТО в кв.м.-----------------------

def limit(lower_bound, value, upper_bound):
	return max(min(value, upper_bound), lower_bound)

#pdiss=100 # примерно равно мощности отопления

def gss_solver(tintown, pdiss, qtown, qhouse, ato, correction = 1):
	# Reading number of unknowns
	n = 3
	
	mid_temp=30
	
	# Making numpy array of n x n+1 size and initializing 
	# to zero for storing augmented matrix
	a = np.zeros((n,n+1))

	# Making numpy array of n size and initializing 
	# to zero for storing solution vector
	x = np.zeros(n)

	# Reading augmented matrix coefficients

	a[0][0]= -qtown *cw
	a[0][1]= -qhouse*cw
	a[0][2]=  qhouse*cw
	
	a[0][3]= -qtown*cw*tintown

	a[1][0]= 0
	a[1][1]=  qhouse*cw-pdiss/2/mid_temp
	a[1][2]= -qhouse*cw-pdiss/2/mid_temp

	a[1][3]=0

	a[2][0]= -qtown*cw - square * ato*correction/2
	a[2][1]= square*ato*correction/2
	a[2][2]= square*ato*correction/2 

	a[2][3]= (square*ato*correction/2 - qtown*cw)*tintown

	# Applying Gauss Elimination
	for i in range(n):
		if a[i][i] == 0.0:
			print('Divide by zero detected!')
			return
		
		for j in range(i+1, n):
			ratio = a[j][i]/a[i][i]
		
			for k in range(n+1):
				a[j][k] = a[j][k] - ratio * a[i][k]

	# Back Substitution
	x[n-1] = a[n-1][n]/a[n-1][n-1]

	for i in range(n-2,-1,-1):
		x[i] = a[i][n]
	
		for j in range(i+1,n):
			x[i] = x[i] - a[i][j]*x[j]
	
		x[i] = x[i]/a[i][i]
	t_rettown = x[0]
	tinhouse = x[1]
#	t_rethouse = x[2]
	# Displaying solution 
	return t_rettown, tinhouse

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
		
		self._pdiss = 100*1000

	def getSupplyDirectTemperature(self):
		return self._program.getInputChannel(self._inputId['supply_direct_temp']).getValue()

	def setSupplyDirectTemperature(self, value):
		self._program.getInputChannel(self._inputId['supply_direct_temp']).setValue(value)

	def getSupplyBackwardTemperature(self):
		return self._program.getInputChannel(self._inputId['supply_backward_temp']).getValue()

	def setSupplyBackwardTemperature(self, value):
		self._program.getInputChannel(self._inputId['supply_backward_temp']).setValue(value)

	def getDirectTemperature(self):
		return self._program.getInputChannel(self._inputId['direct_temp']).getValue()

	def setDirectTemperature(self, value):
		self._program.getInputChannel(self._inputId['direct_temp']).setValue(value)

	def getBackwardTemperature(self):
		return self._program.getInputChannel(self._inputId['backward_temp']).getValue()

	def setBackwardTemperature(self, value):
		self._program.getInputChannel(self._inputId['backward_temp']).setValue(value)

	def getThermalOutputSensor(self):
		return self._program.getInputChannel(self._inputId['thermal_output']).getValue()

	def setThermalOutputSensor(self, value):
		self._program.getInputChannel(self._inputId['thermal_output']).setValue(value)

	def getVolumeFlowSensor(self):
		return self._program.getInputChannel(self._inputId['volume_flow']).getValue()

	def setVolumeFlowSensor(self, value):
		self._program.getInputChannel(self._inputId['volume_flow']).setValue(value)

	def getOutsideRequestSensor(self):
		return self._program.getInputChannel(self._inputId['outside_request']).getValue()

	def setOutsideRequestSensor(self, value):
		self._program.getInputChannel(self._inputId['outside_request']).setValue(value)

	def getTemperature(self):
		return self.getDirectTemperature()

	def getConsumersPower(self):
		return self._control.getConsumersPower(self._program.getId())


	def getPumpState(self, pumpId):
		pump = self._program.getOutputChannel(self._outputId[pumpId])
		if pump.getMapping() is None:
			return 1

		if pump.getValue():
			return 1

		return 0
	
	def getSupplyPumpState(self):
		return self.getPumpState('supply_pump')
	
	def getValveState(self):
		valve        = self._program.getOutputChannel(self._outputId['valve'])
		analog_valve = self._program.getOutputChannel(self._outputId['analog_valve'])
		
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
		
			qtown_max = self.getMaxFlowRateTown()
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
		# тепловой напор - http://ispu.ru/files/u2/Teplovoy_raschet_rekuperativnogo_teploobmennogo_apparata.pdf

		d1 = self.tintown   - self.tinhouse 
		d2 = self.t_rettown - self.t_rethouse
		if abs(d1)>abs(d2):
			d_tmax=d1
			d_tmin=d2
		else:
			d_tmax=d2
			d_tmin=d1
		d_ratio = d_tmax/d_tmin
		if  d_ratio > 2: #!!!!!!!!!!!!!!!!!!!!!!!!!!!
			ddt = (d_tmax - d_tmin) / math.log( d_tmax/d_tmin )
		else :	
			ddt = (d_tmax + d_tmin)/2 
		return ddt, d_ratio
	
	def getMaxFlowRateHouse(self):
		return self._program.getMaxFlowRate1() / 3600 # расход кг/сек в доме постоянный.
	
	def getMaxFlowRateTown(self):
		return self._program.getMaxFlowRate2() / 3600 # расход кг/сек в городе постоянный.

	def computeQHouse(self):
		if self.getCirculationPumpState():
			qhouse = self.getMaxFlowRateHouse()
		else:
			qhouse = 0
		
		return qhouse
	
	def computeTempWithCorrection(self, t_rettown, tinhouse, t_rethouse, qtown, qhouse):
		igss=0
		corr=1
		
		self._pdiss = self.computePdiss(qhouse)
		
		ugolserv = self.getValveState()
		
		ddt, d_ratio = self.ddtf() # температурный напор
		df = qtown/square
		ato = 300 + 3500*math.tanh(df) # !!!корректируем коэффициент теплопередачи по расходу/площадь
		
		print(igss,' ddt %.2f.' % ddt,' d_ratio %.2f.' % d_ratio, ' ugol %.2f.' % ugolserv, 'qtown/S %.2f.' % df, ' rettown %.1f.' % t_rettown,'tinhouse %.2f.' % tinhouse, 'rethous %.1f.' % t_rethouse)

		self.t_rettown, self.tinhouse = gss_solver(self.tintown, self._pdiss, qtown, qhouse, ato)
		if d_ratio > 2.1:
			k = 0
			correction = 1-(d_ratio - 2)/(2.549*d_ratio+2.78) # коэффициент для корректировки среднего логарифмического
			while abs(corr - correction) > 0.05:
				k +=1
				
				ddt, d_ratio = self.ddtf() # температурный напор
				print(k, 'corr %.2f.' % correction,' d_ratio %.2f.' % d_ratio, ' ddt %.2f.' % ddt, ' rettown %.1f.' % t_rettown,'tinhouse %.2f.' % tinhouse, 'rethous %.1f.' % t_rethouse)
				corr = correction
				correction = 1-(d_ratio - 2)/(2.549*d_ratio+2.78)
				print('corr 2 %.2f.' % correction, ' ------------------')
		
	
	def computeTemp(self):
		ugolserv = self.getValveState()
		
		#workaround
#		if ugolserv > 1:
#			ugolserv = 1
			
		if self._init and ugolserv:
			self._init = False
			self.tinhouse  = self.tintown + (self.t_rethouse - self.tintown) * ugolserv
			self.t_rettown = self.tintown*ugolserv+self.tinhouse*(1-ugolserv)
		
		qtown_max = self.getMaxFlowRateTown()
		
		qtown = qtown_max * ugolserv * self.getSupplyPumpState()# расход из города при данном угле сервака

		qhouse = self.computeQHouse()
		
		if qhouse == 0:
			self.t_rettown = self.tintown - 1
		
		if qtown == 0:
			self.tinhouse = self.t_rethouse
			
		if qhouse == 0 or qtown == 0:
			return

		self.computeTempWithCorrection(self.t_rettown, self.tinhouse, self.t_rethouse, qtown, qhouse)
	
	def computePdiss(self, qhouse):
		dT = self.tinhouse - self.t_rethouse
		pdiss = dT * qhouse * cw
		
		dP = self._pdiss - pdiss
		
		dP = limit(-1000, dP, 1000)
		
		self._pdiss -= dP
		
		return self._pdiss
	
	def getFlow(self):
		if self.getCirculationPumpState():
			return self.getMaxFlowRateHouse() / 1000 * 3600# cube per hour
		return 0
	
	def run(self):
		self.tintown    = self.computeSupplyDirectTemperature()
		self.t_rethouse = self.computeBackwardTemperature()
		
		self.computeTemp()
		
		self.setSupplyDirectTemperature  (self.tintown   )
		self.setBackwardTemperature      (self.t_rethouse)
		self.setDirectTemperature        (self.tinhouse  )
		self.setSupplyBackwardTemperature(self.t_rettown )


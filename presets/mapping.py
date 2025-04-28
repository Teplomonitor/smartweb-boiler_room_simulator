
class HeatingCircuitInputMapping(object):
	def __init__(self,
			temperature         = None,
			thermostat          = None,
			outsideRequest      = None,
			pumpControl         = None,
			backwardTemperature = None,
			):
		self._temperature         = temperature        
		self._thermostat          = thermostat         
		self._outsideRequest      = outsideRequest     
		self._pumpControl         = pumpControl        
		self._backwardTemperature = backwardTemperature

	def get(self):
		return [
			self._temperature        ,
			self._thermostat         ,
			self._outsideRequest     ,
			self._pumpControl        ,
			self._backwardTemperature,
		]
	def getTemperature(self): return self._temperature

class HeatingCircuitOutputMapping(object):
	def __init__(self,
			analogValve         = None,
			tptValveOpen        = None,
			tptValveClose       = None,
			pump                = None,
			thermomotor         = None,
			heatchangePump      = None,
			analogPump          = None,
			):
		self._analogValve    = analogValve   
		self._tptValveOpen   = tptValveOpen  
		self._tptValveClose  = tptValveClose 
		self._pump           = pump          
		self._thermomotor    = thermomotor   
		self._heatchangePump = heatchangePump
		self._analogPump     = analogPump    

	def get(self):
		return [
			self._analogValve   ,
			self._tptValveOpen  ,
			self._tptValveClose ,
			self._pump          ,
			self._thermomotor   ,
			self._heatchangePump,
			self._analogPump    ,
		]

class RoomInputMapping(object):
	def __init__(self,
			roomTemperature  = None,
			mode             = None,
			floorTemperature = None,
			wallTemperature  = None,
			humidity         = None,
			co2              = None,
			motion           = None,
			):
		self._roomTemperature  = roomTemperature       
		self._mode             = mode                  
		self._floorTemperature = floorTemperature      
		self._wallTemperature  = wallTemperature       
		self._humidity         = humidity              
		self._co2              = co2                   
		self._motion           = motion           
	def getTemperature(self): return self._roomTemperature

	def get(self):
		return [
			self._roomTemperature ,
			self._mode            ,
			self._floorTemperature,
			self._wallTemperature ,
			self._humidity        ,
			self._co2             ,
			self._motion          ,
		]

class RoomOutputMapping(object):
	def __init__(self,
			relay1       = None,
			relay2       = None,
			relay3       = None,
			signal1      = None,
			signal2      = None,
			signal3      = None,
			ventilation  = None,
			):
		self._relay1      = relay1     
		self._relay2      = relay2     
		self._relay3      = relay3     
		self._signal1     = signal1    
		self._signal2     = signal2    
		self._signal3     = signal3    
		self._ventilation = ventilation

	def get(self):
		return [
			self._relay1     ,
			self._relay2     ,
			self._relay3     ,
			self._signal1    ,
			self._signal2    ,
			self._signal3    ,
			self._ventilation,
		]

class DhwInputMapping(object):
	def __init__(self,
			temperature         = None,
			flow                = None,
			backwardTemperature = None,
			):
		self._temperature         = temperature        
		self._flow                = flow               
		self._backwardTemperature = backwardTemperature  

	def get(self):
		return [
			self._temperature        ,
			self._flow               ,
			self._backwardTemperature,
		]
	def getTemperature(self): return self._temperature

class DhwOutputMapping(object):
	def __init__(self,
			supplyPump       = None,
			circPump         = None,
			analogSupplyPump = None,
			tptValveOpen     = None,
			tptValveClose    = None,
			):
		self._supplyPump       = supplyPump          
		self._circPump         = circPump            
		self._analogSupplyPump = analogSupplyPump    
		self._tptValveOpen     = tptValveOpen        
		self._tptValveClose    = tptValveClose       

	def get(self):
		return [
			self._supplyPump      ,
			self._circPump        ,
			self._analogSupplyPump,
			self._tptValveOpen    ,
			self._tptValveClose   ,
		]

class BoilerInputMapping(object):
	def __init__(self,
			temperature         = None,
			backwardTemperature = None,
			outsideRequest      = None,
			error               = None,
			):
		self._temperature         = temperature        
		self._backwardTemperature = backwardTemperature
		self._outsideRequest      = outsideRequest     
		self._error               = error              

	def get(self):
		return [
			self._temperature        ,
			self._backwardTemperature,
			self._outsideRequest     ,
			self._error              ,
		]
	def getTemperature(self): return self._temperature

class BoilerOutputMapping(object):
	def __init__(self,
			pump                = None,
			burner1             = None,
			burner2             = None,
			power               = None,
			temperature         = None,
			backwardTemperature = None,
			):
		self._pump                = pump               
		self._burner1             = burner1            
		self._burner2             = burner2            
		self._power               = power              
		self._temperature         = temperature        
		self._backwardTemperature = backwardTemperature

	def get(self):
		return [
			self._pump               ,
			self._burner1            ,
			self._burner2            ,
			self._power              ,
			self._temperature        ,
			self._backwardTemperature,
		]

class CascadeInputMapping(object):
	def __init__(self,
			temperature         = None,
			outsideRequest      = None,
			):
		self._temperature    = temperature   
		self._outsideRequest = outsideRequest

	def get(self):
		return [
			self._temperature   ,
			self._outsideRequest,
		]
	def getTemperature(self): return self._temperature

class CascadeOutputMapping(object):
	def __init__(self):
		pass

	def get(self):
		return []

class OatInputMapping(object):
	def __init__(self,
			temperature = None,
			):
		self._temperature = temperature

	def get(self):
		return [
			self._temperature   ,
		]
	def getTemperature(self): return self._temperature

class OatOutputMapping(object):
	def __init__(self):
		pass

	def get(self):
		return []

class SnowMelterInputMapping(object):
	def __init__(self,
			directFlowTemperature = None,
			backwardTemperature   = None,
			plateTemperature      = None,
			snowSensor            = None,
			):
		self._directFlowTemperature = directFlowTemperature
		self._backwardTemperature   = backwardTemperature
		self._plateTemperature      = plateTemperature
		self._snowSensor            = snowSensor

	def get(self):
		return [
			self._directFlowTemperature,
			self._backwardTemperature  ,
			self._plateTemperature     ,
			self._snowSensor           ,
		]
	def getTemperature(self): return self._directFlowTemperature

class SnowMelterOutputMapping(object):
	def __init__(self,
			primaryPump               = None,
			secondaryPump             = None,
			primaryPumpAnalogSignal   = None,
			):
		self._primaryPump             = primaryPump                        
		self._secondaryPump           = secondaryPump                      
		self._primaryPumpAnalogSignal = primaryPumpAnalogSignal
		

	def get(self):
		return [
			self._primaryPump            ,
			self._secondaryPump          ,
			self._primaryPumpAnalogSignal,
		]


class DistrictHeatingInputMapping(object):
	def __init__(self,
			supply_direct_temp   = None,
			supply_backward_temp = None,
			direct_temp          = None,
			backward_temp        = None,
			thermal_output       = None,
			volume_flow          = None,
			outside_request      = None,
			):
		self._supply_direct_temp   = supply_direct_temp  
		self._supply_backward_temp = supply_backward_temp
		self._direct_temp          = direct_temp         
		self._backward_temp        = backward_temp       
		self._thermal_output       = thermal_output      
		self._volume_flow          = volume_flow         
		self._outside_request      = outside_request

	def get(self):
		return [
			self._supply_direct_temp  ,
			self._supply_backward_temp,
			self._direct_temp         ,
			self._backward_temp       ,
			self._thermal_output      ,
			self._volume_flow         ,
			self._outside_request     ,
		]
		
	def getTemperature(self): return self._supply_direct_temp


class DistrictHeatingOutputMapping(object):
	def __init__(self,
			supply_pump      = None,
			circulation_pump = None,
			valve            = None,
			analog_valve     = None,
			):
		self._supply_pump      = supply_pump
		self._circulation_pump = circulation_pump
		self._valve            = valve
		self._analog_valve     = analog_valve
		
	def get(self):
		return [
			self._supply_pump     ,
			self._circulation_pump,
			self._valve           ,
			self._analog_valve    ,
		]



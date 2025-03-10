
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





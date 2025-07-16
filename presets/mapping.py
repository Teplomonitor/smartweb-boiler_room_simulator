
def HeatingCircuitInputMapping(
			temperature         = None,
			thermostat          = None,
			outsideRequest      = None,
			pumpControl         = None,
			backwardTemperature = None,
			):
	return [
		temperature        ,
		thermostat         ,
		outsideRequest     ,
		pumpControl        ,
		backwardTemperature,
	]

def HeatingCircuitOutputMapping(
			analogValve         = None,
			tptValveOpen        = None,
			tptValveClose       = None,
			pump                = None,
			thermomotor         = None,
			heatchangePump      = None,
			analogPump          = None,
			):
	return [
		analogValve   ,
		tptValveOpen  ,
		tptValveClose ,
		pump          ,
		thermomotor   ,
		heatchangePump,
		analogPump    ,
	]

def RoomInputMapping(
			roomTemperature  = None,
			mode             = None,
			floorTemperature = None,
			wallTemperature  = None,
			humidity         = None,
			co2              = None,
			motion           = None,
			):
	return [
		roomTemperature ,
		mode            ,
		floorTemperature,
		wallTemperature ,
		humidity        ,
		co2             ,
		motion          ,
	]

def RoomOutputMapping(
			relay1       = None,
			relay2       = None,
			relay3       = None,
			signal1      = None,
			signal2      = None,
			signal3      = None,
			ventilation  = None,
			):
	return [
		relay1     ,
		relay2     ,
		relay3     ,
		signal1    ,
		signal2    ,
		signal3    ,
		ventilation,
	]

def DhwInputMapping(
			temperature         = None,
			flow                = None,
			backwardTemperature = None,
			):
	return [
		temperature        ,
		flow               ,
		backwardTemperature,
	]

def DhwOutputMapping(
			supplyPump       = None,
			circPump         = None,
			analogSupplyPump = None,
			tptValveOpen     = None,
			tptValveClose    = None,
			):
	return [
		supplyPump      ,
		circPump        ,
		analogSupplyPump,
		tptValveOpen    ,
		tptValveClose   ,
	]

def BoilerInputMapping(
			temperature         = None,
			backwardTemperature = None,
			outsideRequest      = None,
			error               = None,
			):
	return [
		temperature        ,
		backwardTemperature,
		outsideRequest     ,
		error              ,
	]

def BoilerOutputMapping(
			pump                = None,
			burner1             = None,
			burner2             = None,
			power               = None,
			temperature         = None,
			backwardTemperature = None,
			):

	return [
		pump               ,
		burner1            ,
		burner2            ,
		power              ,
		temperature        ,
		backwardTemperature,
	]

def CascadeInputMapping(
			temperature         = None,
			outsideRequest      = None,
			):
	return [
		temperature   ,
		outsideRequest,
	]

def CascadeOutputMapping():
	return []

def OatInputMapping(
			temperature = None,
			):
	return [
		temperature   ,
	]

def OatOutputMapping():
	return []

def SnowMelterInputMapping(
			directFlowTemperature = None,
			backwardTemperature   = None,
			plateTemperature      = None,
			snowSensor            = None,
			):
	return [
		directFlowTemperature,
		backwardTemperature  ,
		plateTemperature     ,
		snowSensor           ,
	]

def SnowMelterOutputMapping(
			primaryPump               = None,
			secondaryPump             = None,
			primaryPumpAnalogSignal   = None,
			):
	return [
		primaryPump            ,
		secondaryPump          ,
		primaryPumpAnalogSignal,
	]


def DistrictHeatingInputMapping(
			supply_direct_temp   = None,
			supply_backward_temp = None,
			direct_temp          = None,
			backward_temp        = None,
			thermal_output       = None,
			volume_flow          = None,
			outside_request      = None,
			):
	return [
		supply_direct_temp  ,
		supply_backward_temp,
		direct_temp         ,
		backward_temp       ,
		thermal_output      ,
		volume_flow         ,
		outside_request     ,
	]

def DistrictHeatingOutputMapping(
			supply_pump      = None,
			circulation_pump = None,
			valve            = None,
			analog_valve     = None,
			):
	return [
		supply_pump     ,
		circulation_pump,
		valve           ,
		analog_valve    ,
	]

def FillingLoopInputMapping(
			pressure_sensor   = None,
			):
	return [
		pressure_sensor,
	]

def FillingLoopOutputMapping(
			filling_loop_output = None,
			alarm_signal_output = None,
			):
	return [
		filling_loop_output,
		alarm_signal_output,
	]

def TptValveInputMapping(
			control_signal   = None,
			):
	return [
		control_signal,
	]

def TptValveOutputMapping(
			valve_open  = None,
			valve_close = None,
			):
	return [
		valve_open,
		valve_close,
	]


def SwimmingPoolInputMapping(
			temperature    = None,
			outsideRequest = None,
			waterLevel     = None,
			flow           = None,
			):
	return [
		temperature   ,
		outsideRequest,
		waterLevel    ,
		flow          ,
	]

def SwimmingPoolOutputMapping(
			circPump          = None,
			supplyPump        = None,
			waterLevelControl = None,
			):
	return [
		supplyPump       ,
		circPump         ,
		waterLevelControl,
	]


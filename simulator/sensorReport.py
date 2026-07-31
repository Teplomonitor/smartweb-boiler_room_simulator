
import smartnet.constants as snc
import smartnet.message   as  sm
from smartnet.units import TEMPERATURE as TEMPERATURE
from smartnet.units import SENSOR_SHORT_VALUE as SENSOR_SHORT_VALUE
from smartnet.units import SENSOR_OPEN_VALUE  as SENSOR_OPEN_VALUE

def reportSensorValue(sensor, bus = None):
	sensorValue   = sensor.get_value()
	sensorMapping = sensor.get_mapping()

	if sensorValue   is None: return False
	if sensorMapping is None: return False

	hostId = sensorMapping.get_host_id()
	
	
	
	isShort = sensor.isShort()
	isOpen  = sensor.isOpen ()
	
	if isShort:
		sensorValue = SENSOR_SHORT_VALUE
	elif isOpen:
		sensorValue = SENSOR_OPEN_VALUE
	else:
		sensorValue = TEMPERATURE(sensorValue)

	value = [
		(sensorValue >> 0) &0xFF,
		(sensorValue >> 8) &0xFF,
		]
	msg = sm.Message(
			snc.ProgramType.CONTROLLER,
			hostId,
			snc.ControllerFunction['GET_OUTPUT_VALUE'],
			snc.RequestFlag.RESPONSE,
			[sensorMapping.get_raw(0), sensorMapping.get_raw(1), value[1], value[0]])
	msg.send(bus = bus)
	return True

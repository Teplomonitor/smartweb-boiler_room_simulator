
import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage
from smartnet.units import TEMPERATURE as TEMPERATURE

def reportSensorValue(sensor, bus = None):
	sensorValue   = sensor.getValue()
	sensorMapping = sensor.getMapping()

	if sensorValue   is None: return False
	if sensorMapping is None: return False

	sensorValue = TEMPERATURE(sensorValue)

	value = [
		(sensorValue >> 0) &0xFF,
		(sensorValue >> 8) &0xFF,
		]
	msg = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			sensorMapping.getHostId(),
			snc.ControllerFunction['GET_OUTPUT_VALUE'],
			snc.requestFlag['RESPONSE'],
			[sensorMapping.getRaw(0), sensorMapping.getRaw(1), value[1], value[0]])
	msg.send(bus = bus)
	return True

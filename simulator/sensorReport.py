
import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage

def reportSensorValue(mapping, sensorValue, bus = None):
	value = [
		(sensorValue >> 0) &0xFF,
		(sensorValue >> 8) &0xFF,
		]
	msg = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			mapping.getHostId(),
			snc.ControllerFunction['GET_OUTPUT_VALUE'],
			snc.requestFlag['RESPONSE'],
			[mapping.getRaw(0), mapping.getRaw(1), value[1], value[0]])
	msg.send(bus = bus)

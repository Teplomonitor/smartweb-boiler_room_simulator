
import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage


def outputRead(programId, outputId, bus = None):
	msg = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			programId,
			snc.RemoteControlFunction['GET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[snc.ProgramType['PROGRAM'], snc.ProgramParameter['OUTPUT'], outputId])
	msg.send(bus = bus)
	return True

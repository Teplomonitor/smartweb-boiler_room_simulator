
import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter as RemoteControlParameter


def outputRead(programId, outputId):
	param = RemoteControlParameter(
			snc.ProgramType['PROGRAM'], 
			snc.ProgramParameter['OUTPUT'],
			parameterIndex = outputId,
			programId = programId)
		
	param.read()
	
	return param.getValue()

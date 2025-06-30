
import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter as RemoteControlParameter


def outputRead(programId, outputId):
	param = RemoteControlParameter(
			snc.ProgramType['PROGRAM'], 
			snc.ProgramParameter['OUTPUT'],
			parameterIndex = outputId)
		
	param.read(programId)
	
	return param.getValue()


from smartnet.remoteControl import RemoteControlParameter as RemoteControlParameter


def outputRead(programId, outputId):
	param = RemoteControlParameter(
			'PROGRAM', 'OUTPUT',
			parameterIndex = outputId,
			programId = programId)
		
	param.read()
	
	return param.getValue()

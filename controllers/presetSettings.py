
import smartnet.constants as snc

class RemoteControlParameter(object):
	def __init__(self,
		programType   ,
		parameterValue):
		self._programType    = programType   
		self._parameterValue = parameterValue

	def write(self, programId):
		print(f'write parameter {id}')
		def generateRequest(id, mapping):
			request = smartnetMessage(
			snc.ProgramType['REMOTE_CONTROL'],
			programId,
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[snc.ProgramType['PROGRAM'], snc.ProgramParameter['OUTPUT_MAPPING'], id, mapping.getRaw(0), mapping.getRaw(1)])
			return request

		def generateRequiredResponse(request):
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse(response):
			if response is None:
				print('bind output timeout')
				return False
			else:
				data = response.getData()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					print('bind ok!')
					return True
				else:
					print('bind error %d' %(result))
					return False


		request        = generateRequest(id, mapping)
		responseFilter = generateRequiredResponse(request)

		response = request.send(responseFilter, 10)

		return handleResponse(response)



class HeatingCircuitSettings(object):
	def __init__(self,
			source         = None,
			):
		self._source         = source

	def get(self):
		return [
			RemoteControlParameter(snc.ConsumerParameter['GENERATOR_ID'], self._source),
		]
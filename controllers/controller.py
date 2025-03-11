'''
@author: admin
'''

import time
from copy import copy

from smartnet.message import Message as smartnetMessage
import smartnet.constants as snc
import controllers.preset

class Controller(object):
	'''
	classdocs
	'''


	def __init__(self, controllerId):
		'''
		Constructor
		'''
		self._controllerId = controllerId

		self._state = 'STATE_IDLE'
		self._programList = []

		self.resetConfig()

		presetList = self.getProgramsAddList()

		for preset in presetList:
			if self.makeNewProgram(preset) == False:
				print('shit!')

		
	def sendProgramAddRequest(self, programType, programId, programScheme):
		print('Send program add request')
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			self._controllerId,
			snc.ControllerFunction['ADD_NEW_PROGRAM'],
			snc.requestFlag['REQUEST'],
			[programType, programId, programScheme])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			response.setData([programType, programId])
			return response

		def handleResponse():
			if response is None:
				print('Program add timeout')
				return False
			else:
				programAddStatus = {
					'STATUS_ADD_PROGRAM_OK'                 : 0,
					'STATUS_ADD_PROGRAM_WRONG_PROGRAM_TYPE' : 1,
					'STATUS_ADD_PROGRAM_TOO_MANY_PROGRAMS'  : 2,
					'STATUS_ADD_PROGRAM_UNDEFINED_ERROR'    : 3,
				}
				data = response.getData()
				if data[2] == programAddStatus['STATUS_ADD_PROGRAM_OK']:
					print('Program add ok!')
					return True
				else:
					print('Program add error %d' %(data[2]))
					return False


		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		response = request.send(responseFilter, 10)

		return handleResponse()

	def makeNewProgram(self, preset):
		return preset.loadPreset(self)

	def getProgramsAddList(self):
		return controllers.preset.getPresetsList()

	def resetConfig(self):
		print('send Controller reset request')
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			self._controllerId,
			snc.ControllerFunction['RESET_PROGRAMS'],
			snc.requestFlag['REQUEST'])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse():
			if response is None:
				print('Program reset timeout')
				return False
			else:
				return True

		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		response = request.send(responseFilter, 10)

		return handleResponse()


	def run(self):
		while True:
			time.sleep(5)

	def addProgram(self, program):
		self._programList.append(program)
	
	def getOutputsNum(self):
		return 0
	
	def getInputsNum(self):
		return 0

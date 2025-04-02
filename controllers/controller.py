'''
@author: admin
'''

import time
from copy import copy

from programs.program import Program as Program
from smartnet.message import Message as smartnetMessage
import smartnet.constants as snc
import presets.preset

class Controller(object):
	'''
	classdocs
	'''


	def __init__(self, controllerId, initPreset):
		'''
		Constructor
		'''
		self._controllerId = controllerId

		self._state = 'STATE_IDLE'
		self._programList = []

		presetList = self.getProgramsAddList()

		if initPreset:
			self.resetConfig()
			for preset in presetList:
				if self.makeNewProgram(preset) == False:
					print('shit!')
		else:
			for preset in presetList:
				prg = Program(preset)
				self.addProgram(prg)

		
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

		response = request.send(responseFilter, 30)

		return handleResponse()

	def makeNewProgram(self, preset):
		return preset.loadPreset(self)

	def getProgramsAddList(self):
		return presets.preset.getPresetsList()

	def getProgramList(self): return self._programList

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

		i = 0
		while i < 3:
			response = request.send(responseFilter, 10)
			result = handleResponse()
			if result:
				break;
			print('retry')
			i = i + 1
			
		return result


	def run(self):
		while True:
			time.sleep(5)

	def addProgram(self, program):
		print('add prg to list')
		self._programList.append(program)
	
	def getOutputsNum(self):
		return 0
	
	def getInputsNum(self):
		return 0

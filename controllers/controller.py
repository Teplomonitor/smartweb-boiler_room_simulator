'''
@author: admin
'''

import time
import can
from threading import Event
from copy import copy

from smartnet.message import Message as smartnetMessage
import smartnet.constants as snc
import controllers.preset

class Controller(can.Listener):
	'''
	classdocs
	'''


	def __init__(self, controllerId, bus):
		'''
		Constructor
		'''
		self._controllerId = controllerId

		self._bus = bus
		self._notifier = can.Notifier(self._bus, [self])
		self._event = Event()
		self._state = 'STATE_IDLE'
		
	def waitEvent(self, state):
		self._state = state
		self._event.wait(timeout=5) # wait for 5 seconds

	def sendProgramAddRequest(self, programType, programId, programScheme):
		print('Send program add request')
		def generateRequest(programType, programId, programScheme):
			request = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			self._controllerId,
			snc.ControllerFunction['ADD_NEW_PROGRAM'],
			snc.requestFlag['REQUEST'],
			[programType, programId, programScheme])
			return request

		def generateRequiredResponse(request):
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			response.setData([programType, programId])
			return response

		def handleResponse(response):
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


		request        = generateRequest(programType, programId, programScheme)
		responseFilter = generateRequiredResponse(request)

		response = request.send(self._bus, responseFilter, 10)

		return handleResponse(response)

	def makeNewProgram(self, preset):
		preset.loadPreset(self)

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

		def generateRequiredResponse(request):
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		request        = generateRequest()
		responseFilter = generateRequiredResponse(request)

		response = request.send(self._bus, responseFilter, 10)

		if response is None:
			print('Program reset timeout')
			return False
		else:
			return True


	def run(self):
		self.resetConfig()

		programList = self.getProgramsAddList()

		for prg in programList:
			self.makeNewProgram(prg)

		self.waitEvent('STATE_WAIT_PROGRAM_ADD')

		if self._state == 'STATE_WAIT_PROGRAM_ADD':
			print('Bad!')
		else:
			print('Good!!')



	def addProgram(self, programType, programId):
		pass
	
	def getOutputsNum(self):
		return 0
	
	def getInputsNum(self):
		return 0

	def on_message_received(self, message):
		msg = smartnetMessage()
		msg.parse(message)

		programType = msg.getProgramType()


		if self._state == 'STATE_WAIT_PROGRAM_ADD':
			if programType == snc.ProgramType['CONTROLLER']:
				print('Good!')
				self.addProgram(12, 34)
				self._state = 'STATE_IDLE'
				self._event.set()
				return

		pass
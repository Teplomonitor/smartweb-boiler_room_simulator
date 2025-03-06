'''
@author: admin
'''

import time
import can
from threading import Event

from smartnet.message import Message as smartnetMessage
import smartnet.constants as snc

class Controller(can.Listener):
	'''
	classdocs
	'''


	def __init__(self, controllerId):
		'''
		Constructor
		'''
		self._controllerId = controllerId

		self._bus = self.createBus()
		self._notifier = can.Notifier(self._bus, [self])
		self._event = Event()
		self._state = 'STATE_IDLE'
		

	def createBus(self):
		#TODO: don't listen own messages
		return can.Bus(receive_own_messages=True)
	
	def waitEvent(self, state):
		self._state = state
		self._event.wait(timeout=5) # wait for 5 seconds

	def sendProgramAddRequest(self, programId, programType):
		data = [23, self._controllerId, 0x03,0x04,0x05]
		message = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			self._controllerId,
			snc.ControllerFunction['ADD_NEW_PROGRAM'],
			1,
			data)

		message.send(self._bus)

	def run(self):
		self.sendProgramAddRequest()
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

		print('Wow!')
		pass
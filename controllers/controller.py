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
		data = [programType, programId, programScheme]
		message = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			self._controllerId,
			snc.ControllerFunction['ADD_NEW_PROGRAM'],
			'REQUEST',
			data)

		message.send(self._bus)

	def getProgramsAddList(self):
		programsList = [
			'OUTDOOR_SENSOR',
			'CASCADE_MANAGER',
			'BOILER',
			'BOILER',
			'BOILER',
			'DHW',
			'DHW',
			'HEATING_CIRCUIT',
			'HEATING_CIRCUIT',
			'HEATING_CIRCUIT',
			'HEATING_CIRCUIT',
			'ROOM_DEVICE',
			'ROOM_DEVICE',
			'ROOM_DEVICE',
			'ROOM_DEVICE',
		]
		pass


	def run(self):

		self.getProgramsAddList()
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
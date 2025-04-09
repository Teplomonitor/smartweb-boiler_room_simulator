'''
Created on 9 апр. 2025 г.

@author: admin
'''

import time
from smartnet.message import Message as smartnetMessage
import smartnet.constants as snc


def sendImHere(controllerId, controllerType):
	msg = smartnetMessage(
		snc.ProgramType['CONTROLLER'],
		controllerId,
		snc.ControllerFunction['I_AM_HERE'],
		snc.requestFlag['RESPONSE'],
		[snc.ControllerType[controllerType],]
		)
	msg.send()
	
	
class ControllerIO(object):
	'''
	classdocs
	'''


	def __init__(self, controllerId, controllerType, controllerTitle):
		'''
		Constructor
		'''
		self._type      = controllerType
		self._id        = controllerId
		self._title     = controllerTitle
		self._time_start = time.time()

	def getType     (self): return self._type
	def getId       (self): return self._id
	def getTitle    (self): return self._title
	

	def on_message_received(self, message):
		if message is None:
			return

		msg = smartnetMessage()
		msg.parse(message)

		if msg is None:
			return
		
		def controllerOutputMappingRequestFilter():
			headerOk = ((msg.getProgramType() == snc.ProgramType['CONTROLLER']) and
					(msg.getFunctionId () == snc.ControllerFunction['GET_RELAY_MAPPING']) and
					(msg.getRequestFlag() == snc.requestFlag['REQUEST']))

			return headerOk

		if controllerOutputMappingRequestFilter():
			controllerId   = msg.getProgramId()

			for ctrl in self._controllerList:
				if ctrl.getId() == controllerId:
					break
			
			
	def run(self):
		dT = time.time() - self._time_start
		if dT > 10:
			self._time_start = time.time()
			for ctrl in self._controllerList:
				sendImHere(ctrl.getId(), ctrl.getType())

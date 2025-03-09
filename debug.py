
import threading
import can
import time

import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage

def createBus():
	#TODO: don't listen own messages
	return can.Bus()

class i_am_here_thread(threading.Thread):
	def __init__(self, thread_name, thread_ID):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._canbus     = createBus()

	def sendImHere(self):
		dummyControllerId = 123
		msg = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			dummyControllerId,
			snc.ControllerFunction['I_AM_HERE'],
			snc.requestFlag['RESPONSE'],
			[snc.ControllerType['SWK'],]
			)
		msg.send(self._canbus)

	def run(self):
		while True:
			time.sleep(10)
			self.sendImHere()

class debug_thread(can.Listener):
	def __init__(self):
		self._canbus     = createBus()
		self._notifier = can.Notifier(self._canbus, [self])

		thread1 = i_am_here_thread("IMH", 1001) 
		thread1.start()

	# helper function to execute the threads
	def on_message_received(self, message):
		msg = smartnetMessage()
		msg.parse(message)

		if message is not None:
			print(f"rx: {message.arbitration_id:08X} - {' '.join(format(x, '02x') for x in message.data)}")

			msg.parse(message)

			if (
				(msg.getProgramType() == snc.ProgramType['CONTROLLER']) and
				(msg.getFunctionId () == snc.ControllerFunction['RESET_PROGRAMS']) and
				(msg.getRequestFlag() == snc.requestFlag['REQUEST'])):
					msg.setRequestFlag(snc.requestFlag['RESPONSE'])
					msg.send(self._canbus)

			
			if (
				(msg.getProgramType() == snc.ProgramType['CONTROLLER']) and
				(msg.getFunctionId () == snc.ControllerFunction['ADD_NEW_PROGRAM']) and
				(msg.getRequestFlag() == snc.requestFlag['REQUEST'])):
					programAddStatus = {
						'STATUS_ADD_PROGRAM_OK'                 : 0,
						'STATUS_ADD_PROGRAM_WRONG_PROGRAM_TYPE' : 1,
						'STATUS_ADD_PROGRAM_TOO_MANY_PROGRAMS'  : 2,
						'STATUS_ADD_PROGRAM_UNDEFINED_ERROR'    : 3,
					}
					msg.setRequestFlag(snc.requestFlag['RESPONSE'])
					data = msg.getData()
					data[2] = programAddStatus['STATUS_ADD_PROGRAM_OK']
					msg.send(self._canbus)




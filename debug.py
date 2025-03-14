
import threading
import can
import time

import smartnet.constants as snc
from smartnet.message import Message as smartnetMessage
from smartnet.message import createBus as createBus


class i_am_here_thread(threading.Thread):
	def __init__(self, thread_name, thread_ID, canbus):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._canbus     = canbus

	def sendImHere(self):
		dummyControllerId = 123
		msg = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			dummyControllerId,
			snc.ControllerFunction['I_AM_HERE'],
			snc.requestFlag['RESPONSE'],
			[snc.ControllerType['SWK'],]
			)
		msg.send(bus = self._canbus)

	def run(self):
		while True:
			self.sendImHere()
			time.sleep(10)

def programsResetFilter(msg):
	return ((msg.getProgramType() == snc.ProgramType['CONTROLLER']) and
			(msg.getFunctionId () == snc.ControllerFunction['RESET_PROGRAMS']) and
			(msg.getRequestFlag() == snc.requestFlag['REQUEST']))

def programAddFilter(msg):
	return ((msg.getProgramType() == snc.ProgramType['CONTROLLER']) and
			(msg.getFunctionId () == snc.ControllerFunction['ADD_NEW_PROGRAM']) and
			(msg.getRequestFlag() == snc.requestFlag['REQUEST']))

def remoteControlRequest(msg):
	return ((msg.getProgramType() == snc.ProgramType['REMOTE_CONTROL']) and
			(msg.getFunctionId () == snc.RemoteControlFunction['SET_PARAMETER_VALUE']) and
			(msg.getRequestFlag() == snc.requestFlag['REQUEST']))

def programInputMappingFilter(msg):
	if not remoteControlRequest(msg):
		return False

	data = msg.getData()
	return ((data[0] == snc.ProgramType['PROGRAM']) and
			(data[1] == snc.ProgramParameter['INPUT_MAPPING']))

def programOutputMappingFilter(msg):
	if not remoteControlRequest(msg):
		return False

	data = msg.getData()
	return ((data[0] == snc.ProgramType['PROGRAM']) and
			(data[1] == snc.ProgramParameter['OUTPUT_MAPPING']))

class debug_thread(can.Listener):
	def __init__(self):
		self._canbus   = createBus()
		self._notifier = can.Notifier(self._canbus, [self])

		thread1 = i_am_here_thread("IMH", 1001, self._canbus)
		#to kill thread on sys.exit()
		thread1.daemon = True
		thread1.start()

	def on_message_received(self, message):
		if message is None:
			return

#		print(f"db: {message.arbitration_id:08X} - {' '.join(format(x, '02x') for x in message.data)}")

		msg = smartnetMessage()
		msg.parse(message)

		if programsResetFilter(msg):
			msg.setRequestFlag(snc.requestFlag['RESPONSE'])
			msg.send(bus = self._canbus)
			return

		if programAddFilter(msg):
			programAddStatus = {
				'STATUS_ADD_PROGRAM_OK'                 : 0,
				'STATUS_ADD_PROGRAM_WRONG_PROGRAM_TYPE' : 1,
				'STATUS_ADD_PROGRAM_TOO_MANY_PROGRAMS'  : 2,
				'STATUS_ADD_PROGRAM_UNDEFINED_ERROR'    : 3,
			}
			msg.setRequestFlag(snc.requestFlag['RESPONSE'])
			data = msg.getData()
			data[2] = programAddStatus['STATUS_ADD_PROGRAM_OK']
			msg.send(bus = self._canbus)
			return

		if remoteControlRequest(msg):
			msg.setRequestFlag(snc.requestFlag['RESPONSE'])
			data = msg.getData()
			data.append(snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK'])
			msg.send(bus = self._canbus)
			return




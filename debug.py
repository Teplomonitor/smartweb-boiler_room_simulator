
import threading
import can

import mainThread

import smartnet.constants as snc
import smartnet.message   as sm


class i_am_here_thread(threading.Thread):
	def __init__(self, thread_name, thread_ID, canbus):
		threading.Thread.__init__(self, name = thread_name)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._canbus     = canbus
		self._controllerId = 123
		self._stop_event = threading.Event()
	def setControllerId(self, controllerId):
		self._controllerId = controllerId
		
	def sendImHere(self):
		msg = sm.Message(
			snc.ProgramType.CONTROLLER,
			self._controllerId,
			snc.ControllerFunction.I_AM_HERE,
			snc.RequestFlag.RESPONSE,
			[snc.ControllerType['SWK'],]
			)
		msg.send(bus = self._canbus)

	def run(self):
		while mainThread.taskEnable() and not self._stop_event.is_set():
			self.sendImHere()
			self._stop_event.wait(10)

def programsResetFilter(msg):
	return ((msg.get_program_type() == snc.ProgramType.CONTROLLER) and
			(msg.getFunctionId () == snc.ControllerFunction.RESET_PROGRAMS) and
			(msg.getRequestFlag() == snc.RequestFlag.REQUEST))

def programAddFilter(msg):
	return ((msg.get_program_type() == snc.ProgramType.CONTROLLER) and
			(msg.getFunctionId () == snc.ControllerFunction.ADD_NEW_PROGRAM) and
			(msg.getRequestFlag() == snc.RequestFlag.REQUEST))

def remoteControlSetRequest(msg):
	return ((msg.get_program_type() == snc.ProgramType.REMOTE_CONTROL) and
			(msg.getFunctionId () == snc.RemoteControlFunction.SET_PARAMETER_VALUE) and
			(msg.getRequestFlag() == snc.RequestFlag.REQUEST))

def remoteControlGetRequest(msg):
	return ((msg.get_program_type() == snc.ProgramType.REMOTE_CONTROL) and
			(msg.getFunctionId () == snc.RemoteControlFunction.GET_PARAMETER_VALUE) and
			(msg.getRequestFlag() == snc.RequestFlag.REQUEST))

def programInputMappingFilter(msg):
	if not remoteControlSetRequest(msg):
		return False

	data = msg.get_data()
	return ((data[0] == snc.ProgramType.PROGRAM) and
			(data[1] == snc.ProgramParameter['INPUT_MAPPING']['id']))

def programOutputMappingFilter(msg):
	if not remoteControlSetRequest(msg):
		return False

	data = msg.get_data()
	return ((data[0] == snc.ProgramType.PROGRAM) and
			(data[1] == snc.ProgramParameter['OUTPUT_MAPPING']['id']))

class debug_thread(can.Listener):
	def __init__(self, requiredControllerId):
		self._canbus   = sm.createBus()
		self._closed = False
		try:
			self._notifier = can.Notifier(self._canbus, [self])
		except BaseException:
			self._canbus.shutdown()
			raise

		thread1 = i_am_here_thread("IMH", 1001, self._canbus)
		self._heartbeat = thread1
		if requiredControllerId != 0:
			thread1.setControllerId(requiredControllerId)
		#to kill thread on sys.exit()
		thread1.daemon = True
		try:
			thread1.start()
		except BaseException:
			self.stop()
			raise

	def stop(self):
		# Notifier.stop also invokes listener.stop; guard against re-entry.
		if self._closed:
			return
		self._closed = True
		self._heartbeat._stop_event.set()
		try:
			if self._heartbeat.ident is not None:
				self._heartbeat.join(5)
			if self._heartbeat.is_alive():
				raise RuntimeError('Debug heartbeat did not stop before the timeout')
		finally:
			try:
				self._notifier.stop(timeout=5)
			finally:
				self._canbus.shutdown()

	def on_message_received(self, message):
		if message is None:
			return

#		print(f"db: {message.arbitration_id:08X} - {' '.join(format(x, '02x') for x in message.data)}")

		msg = sm.Message()
		msg.parse(message)

		if programsResetFilter(msg):
			msg.setRequestFlag(snc.RequestFlag.RESPONSE)
			msg.send(bus = self._canbus)
			return

		if programAddFilter(msg):
			programAddStatus = {
				'STATUS_ADD_PROGRAM_OK'                 : 0,
				'STATUS_ADD_PROGRAM_WRONG_PROGRAM_TYPE' : 1,
				'STATUS_ADD_PROGRAM_TOO_MANY_PROGRAMS'  : 2,
				'STATUS_ADD_PROGRAM_UNDEFINED_ERROR'    : 3,
			}
			msg.setRequestFlag(snc.RequestFlag.RESPONSE)
			data = msg.get_data()
			data[2] = programAddStatus['STATUS_ADD_PROGRAM_OK']
			msg.send(bus = self._canbus)
			return

		if remoteControlSetRequest(msg):
			msg.setRequestFlag(snc.RequestFlag.RESPONSE)
			data = msg.get_data()
			data.append(snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK'])
			msg.send(bus = self._canbus)
			return
		
		if remoteControlGetRequest(msg):
			msg.setRequestFlag(snc.RequestFlag.RESPONSE)
			data = msg.get_data()
			data.extend([0xFF, 0xFF, 0xFF])
			msg.send(bus = self._canbus)
			return
			



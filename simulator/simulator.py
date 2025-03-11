
import threading
import can
import time
import math

import smartnet.constants as snc
from smartnet.message import createBus as createBus
from smartnet.message import Message as smartnetMessage
from controllers.channelMapping import ChannelMapping as Mapping

def TEMPERATURE(val):
	return int(val*10)

def reportSensorValue(mapping, sensorValue, bus = None):
	value = [
		(sensorValue >> 0) &0xFF,
		(sensorValue >> 8) &0xFF,
		]
	msg = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			mapping.getHostId(),
			snc.ControllerFunction['GET_OUTPUT_VALUE'],
			snc.requestFlag['RESPONSE'],
			[mapping.getRaw(0), mapping.getRaw(1), value[1], value[0]])
	msg.send(bus = bus)

class OatSimulator(threading.Thread):
	def __init__(self, thread_name, thread_ID, preset, canbus):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._preset     = preset
		inputs = self._preset.getInputs()
		oatInput = inputs.getOat()
		self._sensorMapping = oatInput
		self._canbus        = canbus
		self._time_start    = time.time()

	def getElapsedTime(self):
		return time.time() - self._time_start

	def reportOat(self, value):
		reportSensorValue(self._sensorMapping, value, self._canbus)

	def computeOat(self):
		pi = 3.14
		oat = math.cos(self.getElapsedTime()/1000.0 + pi/2) * 20
		print(f'oat = {oat}')
		return oat

	def run(self):
		while True:
			self.reportOat(TEMPERATURE(self.computeOat()))
			time.sleep(5)

class Simulator(can.Listener):
	'''
	classdocs
	'''

	def __init__(self, controller):
		'''
		Constructor
		'''
		self._controller = controller

		self._canbus   = createBus()
		self._notifier = can.Notifier(self._canbus, [self])

		programsList = self._controller.getProgramsAddList()

		for program in programsList:
			if program.getType() == snc.ProgramType['OUTDOOR_SENSOR']:
				oatThread = OatSimulator("OAT", program.getId(), program, self._canbus)
				oatThread.daemon = True
				oatThread.start()
				self._oat = oatThread
				break

	def on_message_received(self, message):
		if message is None:
			return

	def run(self):
		while True:
			time.sleep(5)
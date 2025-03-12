
import can
import time

import smartnet.constants as snc
from smartnet.message import createBus as createBus
from controllers.channelMapping import ChannelMapping as Mapping
import simulator.oat

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
				oatThread = simulator.oat.Simulator("OAT", program.getId(), program, self._canbus)
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
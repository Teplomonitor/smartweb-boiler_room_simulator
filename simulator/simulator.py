
import can
import time

import smartnet.constants as snc
from smartnet.message import createBus as createBus
from controllers.channelMapping import ChannelMapping as Mapping
from smartnet.message import Message as smartnetMessage

import simulator.oat
import simulator.boiler
import simulator.cascade
import simulator.heating_circuit
import simulator.room
import simulator.dhw

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

		self._programsList = self._controller.getProgramsAddList()

		simulatorType = {
			snc.ProgramType['OUTDOOR_SENSOR' ] : simulator.oat            .Simulator,
			snc.ProgramType['BOILER'         ] : simulator.boiler         .Simulator,
			snc.ProgramType['CASCADE_MANAGER'] : simulator.cascade        .Simulator,
			snc.ProgramType['ROOM_DEVICE'    ] : simulator.room           .Simulator,
			snc.ProgramType['HEATING_CIRCUIT'] : simulator.heating_circuit.Simulator,

		}

		for program in self._programsList:
			if program.getType() in simulatorType:
				thread = simulatorType[program.getType()](f'{program.getTitle()} {program.getId()}', program.getId(), program, self._canbus)
				thread.daemon = True
				thread.start()

	def on_message_received(self, message):
		if message is None:
			return

		msg = smartnetMessage()

		msg.parse(message)

		def programOutputFilter():
			headerOk = ((msg.getProgramType() == snc.ProgramType['REMOTE_CONTROL']) and
					(msg.getFunctionId () == snc.ControllerFunction['GET_PARAMETER_VALUE']) and
					(msg.getRequestFlag() == snc.requestFlag['MSG_RESPONSE']))

			if headerOk:
				data = msg.getData()
				return ((data[0] == snc.ProgramType['PROGRAM']) and
						(data[1] == snc.ProgramParameter['OUTPUT']))

			return False

		if programOutputFilter():
			programId   = msg.getProgramId()
			outputId    = data[2]
			outputValue = data[3]

			for program in self._programsList:
				if program.getId() == programId:
					program.setOutput(outputId, outputValue)
					break



	def run(self):
		while True:
			time.sleep(5)
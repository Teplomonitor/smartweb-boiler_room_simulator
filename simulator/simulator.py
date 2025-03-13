
import can
import time

import smartnet.constants as snc
from smartnet.message import createBus as createBus
from smartnet.message import Message as smartnetMessage
from simulator.sensorReport import reportSensorValue as reportSensorValue

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

		self._programsList = self._controller.getProgramList()

		simulatorType = {
			'OUTDOOR_SENSOR'  : simulator.oat            .Simulator,
			'BOILER'          : simulator.boiler         .Simulator,
			'CASCADE_MANAGER' : simulator.cascade        .Simulator,
			'ROOM_DEVICE'     : simulator.room           .Simulator,
			'HEATING_CIRCUIT' : simulator.heating_circuit.Simulator,
			'DHW'             : simulator.dhw            .Simulator,
		}

		consumerTypesList = [
			'HEATING_CIRCUIT', 
			'DHW',
		]

		sourceTypesList = [
			'BOILER',
			'CASCADE_MANAGER',
		]

		self._activeProgramsList = []
		self._roomList       = []
		self._consumersList  = []
		self._generatorsList = []
		self._oat = None

		for program in self._programsList:
			if program.getType() in simulatorType:
				self._activeProgramsList.append(program)
				thread = simulatorType[program.getType()](f'{program.getTitle()} {program.getId()}', program.getId(), program, self._canbus, self)
				thread.daemon = True
				thread.start()


		for program in self._activeProgramsList:
			if program.getType() in consumerTypesList:
				self._consumersList.append(program)
				continue

			if program.getType() in sourceTypesList:
				self._generatorsList.append(program)
				continue

			if program.getType() == 'OUTDOOR_SENSOR':
				self._oat = program
				continue

			if program.getType() == 'ROOM_DEVICE':
				self._roomList.append(program)
				continue

	def getActiveProgramsList(self): return self._activeProgramsList
	def getConsumerList      (self): return self._consumersList
	def getSourceList        (self): return self._generatorsList
	def getRoomList          (self): return self._roomList
	def getOat               (self): return self._oat

	def on_message_received(self, message):
		if message is None:
			return

		msg = smartnetMessage()
		msg.parse(message)

		if msg is None:
			return
			
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
			for program in self._programsList:
				for programInput in program.getInputs():
					if reportSensorValue(programInput):
						time.sleep(0.1)

			time.sleep(1)



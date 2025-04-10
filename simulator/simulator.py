
import can
import time

import smartnet.constants as snc
from smartnet.message import createBus as createBus
from smartnet.message import Message as smartnetMessage
from simulator.sensorReport import reportSensorValue as reportSensorValue
from simulator.outputRead import outputRead as outputRead

from controllers.channelMapping import ChannelMapping as ChannelMapping

import simulator.oat
import simulator.boiler
import simulator.cascade
import simulator.heating_circuit
import simulator.room
import simulator.snowmelter
import simulator.dhw



class Simulator(can.Listener):
	'''
	classdocs
	'''

	def __init__(self, controller, controllerIo):
		'''
		Constructor
		'''
		self._controller   = controller
		self._controllerIo = controllerIo

#		self._canbus   = createBus()
		self._canbus   = smartnetMessage._txbus
		
		self._notifier = can.Notifier(self._canbus, [self])

		self._programsList = self._controller.getProgramList()

		simulatorType = {
			'OUTDOOR_SENSOR'  : simulator.oat            .Simulator,
			'BOILER'          : simulator.boiler         .Simulator,
			'CASCADE_MANAGER' : simulator.cascade        .Simulator,
			'ROOM_DEVICE'     : simulator.room           .Simulator,
			'HEATING_CIRCUIT' : simulator.heating_circuit.Simulator,
			'SNOWMELT'        : simulator.snowmelter     .Simulator,
			'DHW'             : simulator.dhw            .Simulator,
		}

		consumerTypesList = [
			'HEATING_CIRCUIT', 
			'SNOWMELT', 
			'DHW',
		]

		sourceTypesList = [
			'BOILER',
			'CASCADE_MANAGER',
		]

		self._simList        = []
		self._roomList       = []
		self._heatingCircuitList = []
		self._consumersList  = []
		self._generatorsList = []
		self._oat = None

		for program in self._programsList:
			i = 0
			for output in program.getOutputs():
				mapping = output.getMapping()
				if mapping:
					
					for ctrlIo in self._controllerIo:
						if (ctrlIo.getId() == mapping.getHostId()) and (mapping.getChannelType() == 'CHANNEL_RELAY'):
							ctrlOutputMapping = ChannelMapping(i, 'CHANNEL_OUTPUT', program.getId())
							ctrlIo.setOutputMapping(mapping.getChannelId(), ctrlOutputMapping)
							ctrlIo.reportOutputMapping(mapping.getChannelId())
					
					outputRead(program.getId(), i)
					time.sleep(0.1)
				i = i + 1

		for program in self._programsList:
			if program.getType() in simulatorType:
				sim = simulatorType[program.getType()](
					f'{program.getTitle()} {program.getId()}',
					 program.getId(), program, self._canbus, self)
				self._simList.append(sim)

		for sim in self._simList:
			program = sim._program

			if program.getType() in consumerTypesList:
				self._consumersList.append(sim)

			if program.getType() in sourceTypesList:
				self._generatorsList.append(sim)

			if program.getType() == 'OUTDOOR_SENSOR':
				self._oat = sim

			if program.getType() == 'ROOM_DEVICE':
				self._roomList.append(sim)
			
			if program.getType() == 'HEATING_CIRCUIT':
				self._heatingCircuitList.append(sim)



	def getConsumerList      (self): return self._consumersList
	def getHeatingCircuitList(self): return self._heatingCircuitList
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
		
#		print(f"rx: {msg.generateHeader():08X} - {' '.join(format(x, '02x') for x in msg._data)}")
		
		def programOutputFilter():
			headerOk = ((msg.getProgramType() == snc.ProgramType['REMOTE_CONTROL']) and
					(msg.getFunctionId () == snc.RemoteControlFunction['GET_PARAMETER_VALUE']) and
					(msg.getRequestFlag() == snc.requestFlag['RESPONSE']))

			if headerOk:
				data = msg.getData()
				return ((data[0] == snc.ProgramType['PROGRAM']) and
						(data[1] == snc.ProgramParameter['OUTPUT']))

			return False

		if programOutputFilter():
			programId   = msg.getProgramId()
			data        = msg.getData()
			outputId    = data[2]
			outputValue = data[3]

			if self._programsList is None:
				return
			for program in self._programsList:
				if program.getId() == programId:
					program.getOutput(outputId).setValue(outputValue)
					break
			return
		
		if self._controllerIo is None:
			return
		for ctrlIo in self._controllerIo:
			ctrlIo.on_message_received(message)
		
	def run(self):
		while True:
			time_start = time.time()
			for sim in self._simList:
				sim.run()

				program = sim._program
				for programInput in program.getInputs():
					if reportSensorValue(programInput):
						time.sleep(0.1)

			for ctrlIo in self._controllerIo:
				ctrlIo.run()
			
			dt = time.time() - time_start
			
			time.sleep(1 - dt)



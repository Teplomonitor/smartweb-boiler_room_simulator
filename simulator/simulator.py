
import time
import threading

import mainThread

import simulator.sensorReport  as ssr
from smartnet.channelMapping import ChannelMapping    as ChannelMapping

import simulator.oat
import simulator.boiler
import simulator.cascade
import simulator.heating_circuit
import simulator.room
import simulator.snowmelter
import simulator.dhw
import simulator.district_heating
import simulator.fillingLoop
import simulator.collector
import simulator.tptValve
import simulator.swimmingPool
import simulator.virtualController
import smartnet.constants as snc

BROADCAST_ID = 0

simulatorType = {
	snc.ProgramType.OUTDOOR_SENSOR   : simulator.oat             .Simulator,
	snc.ProgramType.BOILER           : simulator.boiler          .Simulator,
	snc.ProgramType.CASCADE_MANAGER  : simulator.cascade         .Simulator,
	snc.ProgramType.ROOM_DEVICE      : simulator.room            .Simulator,
	snc.ProgramType.HEATING_CIRCUIT  : simulator.heating_circuit .Simulator,
	snc.ProgramType.SNOWMELT         : simulator.snowmelter      .Simulator,
	snc.ProgramType.DHW              : simulator.dhw             .Simulator,
	snc.ProgramType.DISTRICT_HEATING : simulator.district_heating.Simulator,
	snc.ProgramType.FILLING_LOOP     : simulator.fillingLoop     .Simulator,
	snc.ProgramType.TPT_VALVE_ADAPTER: simulator.tptValve        .Simulator,
	snc.ProgramType.POOL             : simulator.swimmingPool    .Simulator,
	snc.ProgramType.VIRTUAL_CONTROLLER: simulator.virtualController.Simulator,
}

consumerTypesList = [
	snc.ProgramType.HEATING_CIRCUIT,
	snc.ProgramType.SNOWMELT,
	snc.ProgramType.DHW,
	snc.ProgramType.POOL,
]

sourceTypesList = [
	snc.ProgramType.BOILER,
	snc.ProgramType.CASCADE_MANAGER,
	snc.ProgramType.DISTRICT_HEATING,
]


class sensor_report_thread(threading.Thread):
	def __init__(self, simulator):
		threading.Thread.__init__(self, name = 'report_sensors')
		
		self._simulator = simulator
		self.daemon = True
		self.start()
	
	def reportSensorsValues(self):
		ctrlIO = self._simulator.getControllersIOList()
		
		selfIdList = []
		
		for ctr in ctrlIO:
			selfIdList.append(ctr.get_id())
		
		for sim in self._simulator._simList:
			program = sim._program
			for programInput in program.get_inputs().values():
				if programInput.is_mapped() and programInput.get_mapping().get_host_id() in selfIdList:
					if ssr.reportSensorValue(programInput):
						time.sleep(0.1)
						
	def run(self):
		while mainThread.taskEnable():
			self.reportSensorsValues()
			time.sleep(2)

class Simulator(threading.Thread):
	'''
	classdocs
	'''

	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, 'instance'):
			cls.instance = super(Simulator, cls).__new__(cls)
		return cls.instance

	def __init__(self, thread_name = None, thread_ID = None):
		'''
		Constructor
		'''
		if hasattr(self, '_initDone'):
			return
		
		self.clear()
		
		threading.Thread.__init__(self, name = thread_name)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		
		
		self._srt = sensor_report_thread(self)
		
		self._initDone = True
		
		self.daemon = True
		self.start()
	
	def clear(self):
		self._simulator_ready = False
		self._controllerHost = None
		self._controllerIo   = []
		self._simList        = []
		self._roomList       = []
		self._heatingCircuitList = []
		self._consumersList  = []
		self._generatorsList = []
		self._cascadeList    = []
		self._oat = None
		self._collector = None
		
#		time.sleep(2)
		
	def reloadConfig(self, controllerHost, controllerIo):
		self.clear()
		
		self._controllerHost = controllerHost
		self._controllerIo   = controllerIo

		programsList = self._controllerHost.get_program_list()
		
		for program in programsList:
			programId = program.get_id()
			i = 0
			for output in program.get_outputs().values():
				mapping = output.get_mapping()
				if mapping:
					for ctrlIo in self._controllerIo:
						if (ctrlIo.get_id() == mapping.get_host_id()) and (mapping.get_channel_type() == 'CHANNEL_RELAY'):
							ctrlOutputMapping = ChannelMapping(i, 'CHANNEL_OUTPUT', programId)
							ctrlIo.setOutputMapping(mapping.get_channel_id(), ctrlOutputMapping)
							ctrlIo.reportOutputMapping(mapping.get_channel_id())
							
					time.sleep(0.1)
				i = i + 1
				
		for program in programsList:
			programType = program.get_type()
			if programType in simulatorType:
				sim = simulatorType[programType](program, self)
				self._simList.append(sim)
				
		for sim in self._simList:
			program = sim._program
			
			if program.get_type() in consumerTypesList: self._consumersList.append(sim)
			if program.get_type() in sourceTypesList  : self._generatorsList.append(sim)
			if program.get_type() == snc.ProgramType.OUTDOOR_SENSOR : self._oat = sim
			if program.get_type() == snc.ProgramType.ROOM_DEVICE    : self._roomList.append(sim)
			if program.get_type() == snc.ProgramType.HEATING_CIRCUIT: self._heatingCircuitList.append(sim)
			if program.get_type() == snc.ProgramType.CASCADE_MANAGER: self._cascadeList.append(sim)

		self._collector = simulator.collector.Simulator(self)
		self._simulator_ready = True

	def getControllersIOList (self): return self._controllerIo
	def getConsumerList      (self): return self._consumersList
	def getHeatingCircuitList(self): return self._heatingCircuitList
	def getSourceList        (self): return self._generatorsList
	def getRoomList          (self): return self._roomList
	def getCascadeList       (self): return self._cascadeList
	def getOat               (self): return self._oat
	
	def get_consumer_power(self, sourceId):
		programList = self.getConsumerList()
		consumerList = []
		for program in programList:
			sourceList = program._program.get_temperature_source_list()
			if ((sourceId in sourceList) or
				(BROADCAST_ID in sourceList) ):
				consumerList.append(program)

		consumerPower = 0
		for consumer in consumerList:
			consumerPower = consumerPower + consumer.get_power()

		return consumerPower
	
	
	def runProgramSimulators(self):
		try:
			for sim in self._simList:
				sim.run()
		except:
			print('prg sim fault')
			
	def runVirtualControllers(self):
		for ctrlIo in self._controllerIo:
			ctrlIo.run()
			
	def runCollector(self):
		if self._collector:
			self._collector.run()
			
	def run(self):
		while mainThread.taskEnable():
			if not self._simulator_ready:
				time.sleep(1)
				continue
			
			time_start = time.time()
			
			self.runProgramSimulators()
			self.runVirtualControllers()
			self.runCollector()
			
			dt = time.time() - time_start
			
			if dt > 1:
				dt = 1 
			
			time.sleep(1 - dt)
			
			if not self._srt.is_alive():
				print('Oh shi! Sensor report is dead')
				break

		self.clear()

def initIoSimulator():
	simulatorThread = Simulator("simulator thread", 789)
	return simulatorThread


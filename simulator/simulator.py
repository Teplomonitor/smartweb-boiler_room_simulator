
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

BROADCAST_ID = 0

simulatorType = {
	'OUTDOOR_SENSOR'   : simulator.oat             .Simulator,
	'BOILER'           : simulator.boiler          .Simulator,
	'CASCADE_MANAGER'  : simulator.cascade         .Simulator,
	'ROOM_DEVICE'      : simulator.room            .Simulator,
	'HEATING_CIRCUIT'  : simulator.heating_circuit .Simulator,
	'SNOWMELT'         : simulator.snowmelter      .Simulator,
	'DHW'              : simulator.dhw             .Simulator,
	'DISTRICT_HEATING' : simulator.district_heating.Simulator,
	'FILLING_LOOP'     : simulator.fillingLoop     .Simulator,
	'TPT_VALVE_ADAPTER': simulator.tptValve        .Simulator,
	'POOL'             : simulator.swimmingPool    .Simulator,
	'VIRTUAL_CONTROLLER': simulator.virtualController.Simulator,
}

consumerTypesList = [
	'HEATING_CIRCUIT',
	'SNOWMELT',
	'DHW',
	'POOL',
]

sourceTypesList = [
	'BOILER',
	'CASCADE_MANAGER',
	'DISTRICT_HEATING',
]


class sensor_report_thread(threading.Thread):
	def __init__(self, simulator):
		threading.Thread.__init__(self, name = 'report_sensors')
		
		self._simulator = simulator
		self.deamon = True
		self.start()
	
	def reportSensorsValues(self):
		ctrlIO = self._simulator.getControllersIOList()
		
		selfIdList = []
		
		for ctr in ctrlIO:
			selfIdList.append(ctr.get_id())
		
		for sim in self._simulator._simList:
			program = sim._program
			for programInput in program.get_inputs().values():
				if programInput.isMapped() and programInput.getMapping().getHostId() in selfIdList:
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
		
		self.deamon = True
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

		programsList = self._controllerHost.getProgramList()
		
		for program in programsList:
			programId = program.get_id()
			i = 0
			for output in program.get_outputs().values():
				mapping = output.getMapping()
				if mapping:
					for ctrlIo in self._controllerIo:
						if (ctrlIo.get_id() == mapping.getHostId()) and (mapping.getChannelType() == 'CHANNEL_RELAY'):
							ctrlOutputMapping = ChannelMapping(i, 'CHANNEL_OUTPUT', programId)
							ctrlIo.setOutputMapping(mapping.getChannelId(), ctrlOutputMapping)
							ctrlIo.reportOutputMapping(mapping.getChannelId())
							
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
			if program.get_type() == 'OUTDOOR_SENSOR' : self._oat = sim
			if program.get_type() == 'ROOM_DEVICE'    : self._roomList.append(sim)
			if program.get_type() == 'HEATING_CIRCUIT': self._heatingCircuitList.append(sim)
			if program.get_type() == 'CASCADE_MANAGER': self._cascadeList.append(sim)

		self._collector = simulator.collector.Simulator(self)
		self._simulator_ready = True

	def getControllersIOList (self): return self._controllerIo
	def getConsumerList      (self): return self._consumersList
	def getHeatingCircuitList(self): return self._heatingCircuitList
	def getSourceList        (self): return self._generatorsList
	def getRoomList          (self): return self._roomList
	def getCascadeList       (self): return self._cascadeList
	def getOat               (self): return self._oat
	
	def getConsumersPower(self, sourceId):
		programList = self.getConsumerList()
		consumerList = []
		for program in programList:
			sourceList = program._program.get_temperatureSourceList()
			if ((sourceId in sourceList) or
				(BROADCAST_ID in sourceList) ):
				consumerList.append(program)

		consumerPower = 0
		for consumer in consumerList:
			consumerPower = consumerPower + consumer.getPower()

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


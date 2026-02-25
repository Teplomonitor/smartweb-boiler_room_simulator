
import time
import threading
import sys
import config

import presets.preset
from consoleLog import printError as printError
import controllers.search      as ctrlSearch

import smartnet.message as sm
import controllers.controller_io as ccio
import controllers.controller    as cc
import simulator.simulator       as ss

import scenario.scenario as scenario

import debug
import udp.udp as udp

def mock_missing(name):
	def init(self, *args, **kwargs):
		raise ImportError(
			f'The class {name} you tried to call is not importable; '
			f'this is likely due to it not being installed.')
	return type(name, (), {'__init__': init})

try:
	import gui.frame as guiFrameThread
except:
	guiFrameThread = mock_missing('guiFrameThread')

def loadPresetNow(preset):
	programList, controllerIoList = presets.preset.getPresetsList(preset)

	ioSimulator    = ss.Simulator()
	controllerHost = cc.Controller()
	
	ioSimulator.Clear()
	controllerHost.Clear()
	
	controllerHost.initController(True, programList)
	ctrlIo = ccio.initVirtualControllers(controllerIoList)
	ioSimulator.reloadConfig(controllerHost, ctrlIo)
	
	MainThread().setCurrentPreset(preset)
	
class MainThread(threading.Thread):
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, 'instance'):
			cls.instance = super(MainThread, cls).__new__(cls)
		return cls.instance

	def __init__(self, args = None):
		if hasattr(self, '_initDone'):
			return
		
		threading.Thread.__init__(self, name = 'MyMainThread')

		self.configParserInstance = config.ConfigParserInstance()
		
		self._udp_bridge_enable           = int(args.udp)
		self._profile                     = args.profile
		self._scenario                    = args.scenario
		self._debug                       = args.debug
		self._canConfig                   = args.can
		self._debug_thread                = None
		
		preset = self.getCurrentPreset()
		
		self._programPresetList, self._controllerIoList = presets.preset.getPresetsList(preset)
		self._taskStopEvent = threading.Event()
		
		if self._programPresetList is None:
			printError('wrong preset. Exit')
			sys.exit(1)
		
		if args.gui:
			self._guiThread = guiFrameThread.guiThread()
		else:
			self._guiThread = None
			
		self._newPreset = None
		self._saveProgramPlots = threading.Event()

		self._initDone = True
		
		self.deamon = True
		self.start()
	
	def getCANBusConfig(self): return self._canConfig

	def getCurrentPreset(self):   return self.configParserInstance.getParameterValue(self.getProfile(), 'preset')
	def setCurrentPreset(self, preset):  self.configParserInstance.setParameterValue(self.getProfile(), 'preset', preset)
		
	def getProfile(self): return self._profile
	def taskEnable(self): return self._taskStopEvent.is_set() == False
	def taskStop(self): self._taskStopEvent.set()
	def saveProgramPlots(self): self._saveProgramPlots.set()

	def saveProgramPlotsNow(self):
		programList = cc.Controller().getProgramList()
		for prg in programList:
			prg.saveLog()

	def initSimulator(self):
		sm.CanListener()
		
		if self._udp_bridge_enable:
			udp.initUdpBridge(self._udp_bridge_enable)
		
		if self._debug:
			self._debug_thread = debug.debug_thread()
			
		controllerId = ctrlSearch.findOnlineController()
		
		if controllerId is None:
			printError('controller not found. Exit')
			self.taskStop()
			return
		
		ioSimulator    = ss.Simulator("simulator thread", 789)
		controllerHost = cc.Controller(controllerId, self._guiThread)
		
		controllerHost.initController(False, self._programPresetList)
		ctrlIo = ccio.initVirtualControllers(self._controllerIoList)
		ioSimulator.reloadConfig(controllerHost, ctrlIo)
		
		scenario.ScenarioThread(controllerHost, ioSimulator)
		
		if self._scenario != 'none':
			scenario.startScenario(self._scenario)
			
	
	def checkAliveThreads(self):
		if not ss.Simulator().is_alive():
			print('Simulator is dead!')
			return False
		
		if not scenario.ScenarioThread().is_alive():
			print('Scenario is dead!')
			return False
		
		return True
		
	def run(self):
		self.initSimulator()
		
		while self.taskEnable():
			time.sleep(1)
			
			if self._newPreset:
				loadPresetNow(self._newPreset)
				self._newPreset = None

			if self._saveProgramPlots.is_set():
				self._saveProgramPlots.clear()
				self.saveProgramPlotsNow()
			
			if self.checkAliveThreads() == False:
				self.taskStop()
				
			
		self.Clear()

	def Clear(self):
		time.sleep(1)
		
		if self._debug_thread:
			self._debug_thread.stop()
			
		cc.Controller().Clear()
		sm.CanListener().stop()
		
		if self._guiThread:
			self._guiThread.stop()
			
	def loadPreset(self, newPreset):
		self._newPreset = newPreset
	
	def loadPresetDone(self):
		return self._newPreset == None

def taskEnable():
	return MainThread().taskEnable()

def MainStop():
	MainThread().taskStop()
	
	



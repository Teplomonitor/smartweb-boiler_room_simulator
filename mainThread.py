
import time
import threading
import sys
import config

import presets.preset
from consoleLog import printError as printError
from controllers.search        import findOnlineController   as findOnlineController

from smartnet.message          import CanListener            as CanListener
from controllers.controller_io import initVirtualControllers as initVirtualControllers
from controllers.controller    import Controller             as Controller
from simulator.simulator       import Simulator              as Simulator
from scenario.scenario         import ScenarioThread         as ScenarioThread
import debug
from udp.udp import initUdpBridge as initUdpBridge

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

	ioSimulator    = Simulator()
	controllerHost = Controller()
	
	ioSimulator.Clear()
	controllerHost.Clear()
	
	controllerHost.initController(True, programList)
	ctrlIo = initVirtualControllers(controllerIoList)
	ioSimulator.reloadConfig(controllerHost, ctrlIo)
	
class MainThread(threading.Thread):
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, 'instance'):
			cls.instance = super(MainThread, cls).__new__(cls)
		return cls.instance

	def __init__(self, args = None):
		if hasattr(self, '_initDone'):
			return
		
		threading.Thread.__init__(self, name = 'MainThread')

		self.configParserInstance = config.ConfigParserInstance()
		
		self._udp_bridge_enable           = int(args.udp)
		self._profile                     = args.profile
		
		preset = self.configParserInstance.getParameterValue(self._profile, 'preset')
		
		self._scenario                    = args.scenario
		self._programPresetList, self._controllerIoList = presets.preset.getPresetsList(preset)
		self._taskEnable = True
		self._debug = args.debug
		
		if self._programPresetList is None:
			printError('wrong preset. Exit')
			sys.exit(1)
		
		CanListener()
		
		if args.gui:
			self._guiThread = guiFrameThread.guiThread()
		else:
			self._guiThread = None
			
		self._newPreset = None

		self._initDone = True
		
		self.deamon = True
		self.start()
	
	def taskEnable(self):
		return self._taskEnable
	
	def taskStop(self):
		self._taskEnable = False
		
	def initSimulator(self):
		
		if self._udp_bridge_enable:
			initUdpBridge(self._udp_bridge_enable)
		
		if self._debug:
			debug.debug_thread()
			
		controllerId = findOnlineController()
		
		if controllerId is None:
			printError('controller not found. Exit')
			sys.exit(1)
		
		ioSimulator    = Simulator("simulator thread", 789)
		controllerHost = Controller(controllerId, self._guiThread)
		
		controllerHost.initController(False, self._programPresetList)
		ctrlIo = initVirtualControllers(self._controllerIoList)
		ioSimulator.reloadConfig(controllerHost, ctrlIo)
		
		if self._scenario != 'none':
			ScenarioThread(controllerHost, ioSimulator)
		
	def run(self):
		self.initSimulator()
		
		while self.taskEnable():
			time.sleep(1)
			
			if self._newPreset:
				loadPresetNow(self._newPreset)
				
				self.configParserInstance.setParameterValue(self._profile, 'preset', self._newPreset)
				
				self._newPreset = None
			
	def loadPreset(self, newPreset):
		self._newPreset = newPreset
			

def taskEnable():
	return MainThread().taskEnable()

def MainStop():
	MainThread().taskStop()
	
	time.sleep(1)
	
	Simulator().Clear()
	Controller().Clear()
	
	CanListener().stop()
	



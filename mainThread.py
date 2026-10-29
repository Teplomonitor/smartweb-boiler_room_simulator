
import threading
import config

import presets.preset
from consoleLog import print_error as print_error
import controllers.search      as ctrlSearch

import smartnet.message as sm
import controllers.controller_io as ccio
import controllers.controller    as cc
import simulator.simulator       as ss
import consoleLog

import scenario.scenario as scenario

import debug
import udp.udp as udp

THREAD_JOIN_TIMEOUT = 5.0
_application = None


def register_application(application):
	global _application
	if _application is not None and _application is not application:
		raise RuntimeError('An application session is already active')
	_application = application


def unregister_application(application):
	global _application
	if _application is application:
		_application = None


def MainThread(args=None):
	"""Compatibility accessor; no-argument calls never create services."""
	if _application is None:
		if args is None:
			raise RuntimeError('Application has not been started')
		from application import Application
		application = Application(args)
		application.start()
	if _application.worker is None:
		raise RuntimeError('Application worker has not been initialized')
	return _application.worker

def loadPresetNow(preset):
	main_thread = MainThread()
	gui = main_thread._guiThread
	if gui:
		gui.set_preset_loading(True)
	try:
		programList, controllerIoList = presets.preset.get_presets_list(preset)

		ioSimulator    = ss.Simulator()
		controllerHost = cc.Controller()
		
		ioSimulator.clear()
		controllerHost.clear()
		
		controllerHost.initController(True, programList)
		ctrlIo = ccio.initVirtualControllers(controllerIoList)
		ioSimulator.reloadConfig(controllerHost, ctrlIo)
		
		main_thread.setCurrentPreset(preset)
		return True
	except Exception:
		print_error('Wrong preset!!!')
		return False
	finally:
		if gui:
			gui.set_preset_loading(False)
	
class ApplicationWorker(threading.Thread):
	def __init__(self, args, gui, stop_event):
		threading.Thread.__init__(self, name = 'MyMainThread')
		self._taskStopEvent = stop_event
		self._guiThread = gui
		self._simulator = None
		self._controller = None
		self._scenario_thread = None
		self._can_listener = None
		self._udp_bridge = None
		self.error = None
		self.ready_event = threading.Event()

		self.configParserInstance = config.ConfigParserInstance()
		
		self._udp_bridge_enable           = int(args.udp)
		self._profile                     = args.profile
		self._scenario                    = args.scenario
		self._debug                       = args.debug
		self._canConfig                   = args.can
		self._debug_thread                = None
		self._controllerId                = int(args.id)
		
		self._lastPreset                    = None
		
		self._programPresetList = []
		self._controllerIoList  = []
		
		if args.preset:
			self._newPreset = args.preset
		else:
			self._newPreset = None
			preset = self.getCurrentPreset()
		
			result = presets.preset.get_presets_list(preset)
			
			if result is None:
				print_error('wrong preset')
			else:
				self._programPresetList, self._controllerIoList = result
			
			if self._programPresetList is None:
				print_error('wrong preset. Exit')
				raise ValueError('Invalid preset')
		
		self._saveProgramPlots = threading.Event()

		self.daemon = True
	
	def getCANBusConfig(self): return self._canConfig

	def getCurrentPreset(self):   return self.configParserInstance.getParameterValue(self.getProfile(), 'preset')
	def setCurrentPreset(self, preset):  self.configParserInstance.setParameterValue(self.getProfile(), 'preset', preset)
		
	def getProfile(self): return self._profile
	def taskEnable(self): return self._taskStopEvent.is_set() == False
	def taskStop(self): self._taskStopEvent.set()
	def saveProgramPlots(self): self._saveProgramPlots.set()

	def saveProgramPlotsNow(self):
		programList = cc.Controller().get_program_list()
		for prg in programList:
			prg.save_log()
		consoleLog.save_log()

	def initSimulator(self):
		self._can_listener = sm.CanListener()
		
		if self._udp_bridge_enable:
			self._udp_bridge = udp.init_udp_bridge(self._udp_bridge_enable)
		
		if self._debug:
			self._debug_thread = debug.debug_thread(self._controllerId)
			
		controllerId = ctrlSearch.findOnlineController(self._controllerId)
		if not self.taskEnable():
			return
		
		if controllerId is None:
			print_error('controller not found. Exit')
			self.error = RuntimeError('Controller not found')
			self.taskStop()
			return
		
		ioSimulator    = ss.Simulator("simulator thread", 789)
		self._simulator = ioSimulator
		controllerHost = cc.Controller(controllerId, self._guiThread)
		self._controller = controllerHost
		
		controllerHost.initController(False, self._programPresetList)
		if not self.taskEnable():
			return
		ctrlIo = ccio.initVirtualControllers(self._controllerIoList)
		ioSimulator.reloadConfig(controllerHost, ctrlIo)
		if not self.taskEnable():
			return
		
		self._scenario_thread = scenario.ScenarioThread(controllerHost, ioSimulator)
		self.ready_event.set()
		
		if self._scenario != 'none':
			scenario.start_scenario(self._scenario)
			
	
	def checkAliveThreads(self):
		if self._simulator is None or not self._simulator.is_alive():
			print_error('Simulator is dead!')
			return False
		
		if self._scenario_thread is None or not self._scenario_thread.is_alive():
			print_error('Scenario is dead!')
			return False
		
		return True
		
	def run(self):
		try:
			if self.taskEnable():
				self.initSimulator()
			while not self._taskStopEvent.wait(1):
				if self._newPreset:
					if loadPresetNow(self._newPreset):
						self._lastPreset = self._newPreset
					self._newPreset = None
				if self._saveProgramPlots.is_set():
					self._saveProgramPlots.clear()
					self.saveProgramPlotsNow()
				if not self.checkAliveThreads():
					self.taskStop()
		except Exception as exc:
			self.error = exc
			print_error(f'Application worker failed: {exc!r}')
		finally:
			self.taskStop()
			self.clear()

	def clear(self):
		# Use owned references only: cleanup must never create a service.
		def cleanup(name, action):
			try:
				action()
			except Exception as exc:
				self.error = self.error or exc
				print_error(f'Failed to stop {name}: {exc!r}')

		def join_thread(thread):
			thread.join(THREAD_JOIN_TIMEOUT)
			if thread.is_alive():
				raise RuntimeError(f'{thread.name} did not stop before the timeout')

		if self._scenario_thread:
			cleanup('scenario', lambda: join_thread(self._scenario_thread))
		if self._simulator:
			cleanup('simulator', lambda: join_thread(self._simulator))
			cleanup('sensor reporting', lambda: join_thread(self._simulator._srt))
		users = (self._scenario_thread, self._simulator,
			self._simulator._srt if self._simulator else None)
		if not any(thread and thread.is_alive() for thread in users):
			if self._controller:
				cleanup('controller', self._controller.clear)
			if self._simulator:
				cleanup('simulator state', self._simulator.clear)
		if self._debug_thread:
			cleanup('debug responder', self._debug_thread.stop)
		if self._udp_bridge:
			cleanup('UDP bridge', self._udp_bridge.stop)
		if self._can_listener:
			cleanup('CAN listener', self._can_listener.close)
		if self._guiThread:
			cleanup('GUI', self._guiThread.stop)
			
	def loadPreset(self, newPreset):
		if newPreset == self._lastPreset:
			print('Preset is already loaded')
			return
		self._newPreset = newPreset
	
	def loadPresetDone(self):
		return self._newPreset == None

def taskEnable():
	return _application is not None and not _application.stop_event.is_set()

def MainStop():
	if _application is not None:
		_application.request_stop()
	
	



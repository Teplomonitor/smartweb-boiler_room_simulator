'''
@author: admin
'''

import can
import json
import os
import time
import threading

import mainThread
from consoleLog import print_error
from smartnet.can_adapter import protect_gs_usb_receive, resolve_bus_config


FRAME_LOG_INTERVAL = 10.0
FRAME_LOG_SAMPLES = 3
SEND_ATTEMPTS = 10
SEND_RETRY_DELAY = 1.0


class CanFrameDiagnostics:
	"""Per-connection counters; never print one line per frame indefinitely."""
	def __init__(self, context):
		self.context = context
		self.counts = {'standard': 0, 'remote': 0, 'error': 0, 'fd': 0}
		self.rejected = 0
		self.accepted = 0
		self.last_log = None

	def reject(self, frame):
		self.rejected += 1
		self.counts['standard'] += not frame.is_extended_id
		self.counts['remote'] += frame.is_remote_frame
		self.counts['error'] += frame.is_error_frame
		self.counts['fd'] += frame.is_fd
		now = time.monotonic()
		if (self.rejected > FRAME_LOG_SAMPLES and self.last_log is not None
				and now - self.last_log < FRAME_LOG_INTERVAL):
			return
		self.last_log = now
		print_error(f'CAN {self.context}: rejected frame '
			f'ID=0x{frame.arbitration_id:08X} EXT={int(frame.is_extended_id)} '
			f'RTR={int(frame.is_remote_frame)} ERR={int(frame.is_error_frame)} '
			f'FD={int(frame.is_fd)} RX={int(frame.is_rx)} DLC={frame.dlc} '
			f'data={bytes(frame.data).hex(" ")} timestamp={frame.timestamp:.6f}; '
			f'rejected={self.rejected} accepted={self.accepted} counts={self.counts}')



def mock_missing(name):
	def init(self, *args, **kwargs):
		raise ImportError(
			f'The class {name} you tried to call is not importable; '
			f'this is likely due to it not being installed.')
	return type(name, (), {'__init__': init})

try:
	import candle
except:
	candle = mock_missing('guiFrameThread')




def createBus(canConfig = None):
	if not canConfig:
		canConfig = mainThread.MainThread().getCANBusConfig()

	if canConfig == 'none':
		return can.Bus()

	location = os.environ.get('BRS_GS_USB_LOCATION')
	if location:
		try:
			location = json.loads(location)
		except (TypeError, ValueError) as exc:
			raise ValueError(f'{canConfig}: invalid assigned GS-USB location') from exc
		if not isinstance(location, dict):
			raise ValueError(f'{canConfig}: invalid assigned GS-USB location')
		config = resolve_bus_config(canConfig, location=location)
	else:
		config = resolve_bus_config(canConfig)
	bus = can.Bus(**config)
	bus._brs_can_context = canConfig
	if config.get('interface') == 'gs_usb':
		try:
			protect_gs_usb_receive(bus, canConfig, mainThread.report_can_failure)
		except BaseException:
			bus.shutdown()
			raise
	return bus


class CanBusInterface(object):
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, 'instance'):
			cls.instance = super(CanBusInterface, cls).__new__(cls)
		return cls.instance

	def __init__(self, canConfig = None):
		if hasattr(self, '_initDone'):
			return
		
		self._canbus   = createBus(canConfig)
	
		self._initDone = True
	
	def get(self): return self._canbus


class Message(object):
	'''
	classdocs
	'''

	def __init__(self, programType=None, programId=None, functionId=None, request=None, data=None):
		'''
		Constructor
		'''
		self._programType = programType
		self._programId   = programId
		self._functionId  = functionId
		self._requestFlag     = request
		self._responseMessage = None
		self._responseFilter  = None
		self._data        = data
		
	def __del__(self):
		if self._responseFilter:
			CanListener.unsubscribe(self)
		
	def __copy__(self):
		return type(self)(self._programType, self._programId, self._functionId, self._requestFlag, self._data)
	
	def get_program_type(self): return self._programType
	def getProgramId  (self): return self._programId
	def getFunctionId (self): return self._functionId
	def getRequestFlag(self): return self._requestFlag
	def get_data       (self): return self._data
	def getHeader     (self): return self.generateHeader()

	def setProgramType(self, value): self._programType = value
	def setProgramId  (self, value): self._programId   = value
	def setFunctionId (self, value): self._functionId  = value
	def setRequestFlag(self, value): self._requestFlag     = value
	def setData       (self, value): self._data        = value
	def setHeader     (self, value): self.parseHeader(value)

	def generateHeader(self):
		byte0 = self._programType
		byte1 = self._programId
		byte2 = self._functionId
		byte3 = self._requestFlag

		header = (
			(byte0 <<  0) |
			(byte1 <<  8) |
			(byte2 << 16) |
			(byte3 << 24))

		return header

	def parseHeader(self, header):
		byte0 = (header >>  0) & 0xFF
		byte1 = (header >>  8) & 0xFF
		byte2 = (header >> 16) & 0xFF
		byte3 = (header >> 24) & 0xFF
		
		self._programType = byte0
		self._programId   = byte1
		self._functionId  = byte2
		self._requestFlag     = byte3
		
	def smartNetToCanMsg(self):
		header = self.generateHeader()

		msg = can.Message(
			timestamp      = time.time(),
			arbitration_id = header,
			data           = self._data,
			is_extended_id = True
		)
		return msg

	def compare(self, responseFilter):
		if responseFilter is None:
			return False
		
		val = responseFilter.getRequestFlag()
		
		if (val is not None) and (val != self.getRequestFlag()): return False

		val = responseFilter.get_program_type()
		if (val is not None) and (val != self.get_program_type()): return False

		val = responseFilter.getProgramId()
		if (val is not None) and (val != self.getProgramId()  ): return False

		val = responseFilter.getFunctionId()
		if (val is not None) and (val != self.getFunctionId() ): return False

		val = responseFilter.get_data()
		if val is not None:
			val_size = len(val)
			data = self.get_data()
			int_array = [byte for byte in data]
			data_cut = int_array[:val_size]

			if val == data_cut:
#				print('good')
				pass
			else:
#				print('Oh!')
				return False

		return True
	
	def on_can_message_received(self, msg):
		if msg.compare(self._responseFilter):
			self._responseMessage = msg
			
	
	def send(self, responseFilter = None, timeout = None, bus = None):
		msg = self.smartNetToCanMsg()

#		print(f"tx: {msg.arbitration_id:08X} - {' '.join(format(x, '02x') for x in msg.data)}")

		if bus:
			txbus = bus
		else:
			txbus = CanBusInterface().get()
		application = getattr(mainThread, '_application', None)
		stop_event = getattr(application, 'stop_event', None)
		i = 0
		while True:
			if stop_event is not None and stop_event.is_set():
				return None
			try:
				txbus.send(msg)
				break
			except can.CanError as e:
				i += 1
				context = getattr(txbus, '_brs_can_context', txbus.channel_info)
				detail = f'{e!r}; cause={e.__cause__!r}'
				if i == 1:
					print_error(f'CAN {context}: send failed, retrying: {detail}')
				if i >= SEND_ATTEMPTS:
					error = RuntimeError(f'CAN {context}: send failed after {i} attempts: {detail}')
					if getattr(txbus, '_brs_gs_usb', False):
						mainThread.report_can_failure(error)
					else:
						print_error(str(error))
					return None
				if stop_event is not None:
					if stop_event.wait(SEND_RETRY_DELAY):
						return None
				else:
					time.sleep(SEND_RETRY_DELAY)
		
		if responseFilter is None:
			return None
		
		return self.recv(responseFilter, timeout)

	def recv(self, responseFilter, timeout = 60):
		self._responseFilter = responseFilter
		
		if self._responseFilter:
			CanListener.subscribe(self)
		else:
			return None
		
		start_time = time.time()
		
		while mainThread.taskEnable():
			if (time.time() - start_time) > timeout:
				break
			
			if self._responseMessage:
				break
			
			time.sleep(0.1)
		
		CanListener.unsubscribe(self)
		msg = self._responseMessage
		self._responseFilter  = None
		self._responseMessage = None
		return msg

	def parse(self, message):
		"""Return whether a classic extended data frame was decoded."""
		if (message is None or not message.is_extended_id or message.is_remote_frame
				or message.is_error_frame or message.is_fd):
			self._programType = self._programId = self._functionId = self._requestFlag = None
			self._data = None
			return False
		
		self.parseHeader(message.arbitration_id)
		self._data = message.data
		return True
	

	@staticmethod
	def exit():
		CanBusInterface().get().shutdown()

class CanListener(can.Listener):
	_listeners   = []
	_listeners_lock = threading.Lock()
	
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, 'instance'):
			cls.instance = super(CanListener, cls).__new__(cls)
		return cls.instance

	def __init__(self):
		if hasattr(self, '_initDone'):
			return
		
		self._canbus   = CanBusInterface().get()
		self._frame_diagnostics = CanFrameDiagnostics(
			getattr(self._canbus, '_brs_can_context', self._canbus.channel_info))
		try:
			self._notifier = can.Notifier(self._canbus, [self])
		except BaseException:
			self._canbus.shutdown()
			raise
		self._closed = False
	
		self._initDone = True

	def close(self):
		if self._closed:
			return
		self._closed = True
		try:
			self._notifier.stop(timeout=5)
		finally:
			self._canbus.shutdown()
		
	@staticmethod
	def countListeners():
		i = 0
		
		for __ in CanListener._listeners:
			i += 1
		
		print(f'CL={i}')
		
	@staticmethod
	def subscribe(listener):
		with CanListener._listeners_lock:
			if listener not in CanListener._listeners:
				CanListener._listeners.append(listener)
#		CanListener.countListeners()
		
		
	@staticmethod
	def unsubscribe(listener):
		with CanListener._listeners_lock:
			if listener in CanListener._listeners:
				CanListener._listeners.remove(listener)
#		CanListener.countListeners()
		
	def on_message_received(self, message):
		if message is None:
			return

		msg = Message()
		if not msg.parse(message):
			self._frame_diagnostics.reject(message)
			return
		self._frame_diagnostics.accepted += 1
		
		with CanListener._listeners_lock:
			listeners = tuple(CanListener._listeners)
		for listener in listeners:
			listener.on_can_message_received(msg)
		


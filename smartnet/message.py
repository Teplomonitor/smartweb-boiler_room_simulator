'''
@author: admin
'''

import can
import time

def createBus():
	return can.Bus()

class Message(object):
	'''
	classdocs
	'''
	#this for debug purpose. We need to hear own messages
	_rxbus = createBus()
#	_txbus = createBus()
	_txbus = _rxbus

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
	
	def getProgramType(self): return self._programType
	def getProgramId  (self): return self._programId
	def getFunctionId (self): return self._functionId
	def getRequestFlag(self): return self._requestFlag
	def getData       (self): return self._data
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
		if (val is not None) and (val is not self.getRequestFlag()): return False

		val = responseFilter.getProgramType()
		if (val is not None) and (val is not self.getProgramType()): return False

		val = responseFilter.getProgramId()
		if (val is not None) and (val is not self.getProgramId()  ): return False

		val = responseFilter.getFunctionId()
		if (val is not None) and (val is not self.getFunctionId() ): return False

		val = responseFilter.getData()
		if val is not None:
			val_size = len(val)
			data = self.getData()
			int_array = [byte for byte in data]
			data_cut = int_array[:val_size]

			if val == data_cut:
#				print('good')
				pass
			else:
#				print('Oh!')
				return False

		return True
	
	def OnCanMessageReceived(self, msg):
		if msg.compare(self._responseFilter):
			self._responseMessage = msg
			
	
	def send(self, responseFilter = None, timeout = None, bus = None):
		msg = self.smartNetToCanMsg()

#		print(f"tx: {msg.arbitration_id:08X} - {' '.join(format(x, '02x') for x in msg.data)}")

		if bus:
			txbus = bus
		else:
			txbus = Message._txbus
		
		i = 0
		while True:
			try:
				txbus.send(msg)
				break
			except can.CanError as e:
				print(f"CAN error: {e}")
				i += 1

				if i >= 10:
					print('fail to send')
					return None

				time.sleep(1)

		return self.recv(responseFilter, timeout)

	def recv(self, responseFilter, timeout = 60):
		self._responseFilter = responseFilter
		
		if self._responseFilter:
			CanListener.subscribe(self)
		else:
			return
		
		start_time = time.time()
		
		while True:
			if (time.time() - start_time) > timeout:
				break
			
			if self._responseMessage:
				break
			
			time.sleep(0.1)
		
		self._responseFilter = None
		CanListener.unsubscribe(self)
		
		return self._responseMessage

	def parse(self, message):
		if not message.is_extended_id or message.is_remote_frame:
			print('wrong message type')
			return
		
		self.parseHeader(message.arbitration_id)
		self._data = message.data
	

	@staticmethod
	def exit():
		Message._txbus.shutdown()
		Message._rxbus.shutdown()

class CanListener(can.Listener):
	_listeners   = []
	_lockSubscribe = 0
	
	def __init__(self):
	#	self._canbus   = createBus()
		self._canbus   = Message._txbus
		self._notifier = can.Notifier(self._canbus, [self])
	
	@staticmethod
	def countListeners():
		i = 0
		
		for __ in CanListener._listeners:
			i += 1
		
		print(f'CL={i}')
		
	@staticmethod
	def subscribe(listener):
		if listener in CanListener._listeners:
			return
		
		while CanListener._lockSubscribe:
			time.sleep(0.1)
		
		CanListener._listeners.append(listener)
#		CanListener.countListeners()
		
		
	@staticmethod
	def unsubscribe(listener):
		while CanListener._lockSubscribe:
			time.sleep(0.1)
		if listener in CanListener._listeners:
			CanListener._listeners.remove(listener)
#		CanListener.countListeners()
		
	def on_message_received(self, message):
		if message is None:
			return

		msg = Message()
		msg.parse(message)

		if msg is None:
			return
		
		i = 0
		
		for listener in CanListener._listeners:
			i += 1
			
#		print(f"rx: {msg.generateHeader():08X} - {' '.join(format(x, '02x') for x in msg._data)} s = {i}")

		CanListener._lockSubscribe = 1
		for listener in CanListener._listeners:
			listener.OnCanMessageReceived(msg)
		CanListener._lockSubscribe = 0
		


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
	_txbus = createBus()

	def __init__(self, programType=None, programId=None, functionId=None, request=None, data=None):
		'''
		Constructor
		'''
		self._programType = programType
		self._programId   = programId
		self._functionId  = functionId
		self._request     = request
		self._data        = data
	def __copy__(self):
		return type(self)(self._programType, self._programId, self._functionId, self._request, self._data)
	
	def getProgramType(self): return self._programType
	def getProgramId  (self): return self._programId
	def getFunctionId (self): return self._functionId
	def getRequestFlag(self): return self._request
	def getData       (self): return self._data

	def setProgramType(self, value): self._programType = value
	def setProgramId  (self, value): self._programId   = value
	def setFunctionId (self, value): self._functionId  = value
	def setRequestFlag(self, value): self._request     = value
	def setData       (self, value): self._data        = value

	def generateHeader(self):
		byte0 = self._programType
		byte1 = self._programId
		byte2 = self._functionId
		byte3 = self._request

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
		self._request     = byte3
		
	def smartNetToCanMsg(self):
		header = self.generateHeader()

		msg = can.Message(
			arbitration_id = header,
			data           = self._data,
			is_extended_id = True
		)
		return msg

	def compare(self, responseFilter):
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


	def send(self, responseFilter = None, timeout = None, bus = None):
		msg = self.smartNetToCanMsg()

		print(f"tx: {msg.arbitration_id:08X} - {' '.join(format(x, '02x') for x in msg.data)}")

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
				i = i + 1

				if i >= 10:
					print('fail to send')
					return None

				time.sleep(1)



		if responseFilter:
			return Message.recv(timeout, responseFilter, txbus)

	@staticmethod
	def recv(timeout = None, messageFilter = None, bus = None):
		start_time = time.time()
		snmsg = Message()

		if bus:
			rxbus = bus
		else:
			rxbus = Message._rxbus

		while True:
			try:
				# Read a message from the CAN bus
				message = rxbus.recv(timeout)
			except can.CanError as e:
				print(f"CAN error: {e}")
				return None

			if timeout:
				if (time.time() - start_time) > timeout:
					return None

			if message:
				print(f"rx: {message.arbitration_id:08X} - {' '.join(format(x, '02x') for x in message.data)}")

				snmsg.parse(message)
				if messageFilter:
					if snmsg.compare(messageFilter):
						return snmsg
					else:
						continue
				return snmsg
			return None

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

'''
@author: admin
'''

import can


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
		self._request     = request
		self._data        = data
	
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
		if self._request == 'REQUEST':
			flag = 0x00
		else:
			flag = 0x10

		byte0 = self._programType
		byte1 = self._programId
		byte2 = self._functionId
		byte3 = flag

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
		self._request     = 'RESPONSE' if (byte3 & 0x10) != 0 else 'REQUEST'
		
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
			data_cut = data[:val_size]
			if val is not data_cut:
				return False

		return True


	def waitResponse(self, bus, responseFilter, timeout = None):
		smartnet = Message()
		while True:
			# Read a message from the CAN bus
			message = bus.recv(timeout)

			if message is not None:
				smartnet.parse(message)
				if smartnet.compare(responseFilter):
					return smartnet
			else:
				return None


	def send(self, bus = None, responseFilter = None, timeout = None):
		msg = self.smartNetToCanMsg()

		if not bus:
			bus = can.Bus()

		bus.send(msg)

		if responseFilter:
			response = self.waitResponse(bus, responseFilter, timeout)
			return response
			
	def parse(self, message):
		if not message.is_extended_id or message.is_remote_frame:
			print('wrong message type')
			return
		
		self.parseHeader(message.arbitration_id)
		self._data = message.data
	
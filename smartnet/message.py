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
	
	def getProgramType(self):
		return self._programType
	def getProgramId(self):
		return self._programId
	def getFunctionId(self):
		return self._functionId
	def getRequestFlag(self):
		return self._request
	def getData(self):
		return self._data

	def generateHeader(self):
		if self._request:
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
		self._request     = (byte3 & 0x10) != 0
		
	def send(self, bus=None):
		header = self.generateHeader()

		
		msg = can.Message(
			arbitration_id =header,
			data           =self._data,
			is_extended_id =True
		)

		if bus:
			bus.send(msg)
			return


		#bus config loaded from ~/can.conf file
		#if you don't have it you should make one
		#https://python-can.readthedocs.io/en/stable/configuration.html
		with can.Bus() as bus:
			bus.send(msg)
			
	def parse(self, message):
		if not message.is_extended_id or message.is_remote_frame:
			print('wrong message type')
			return
		
		self.parseHeader(message.arbitration_id)
		self._data = message.data
		
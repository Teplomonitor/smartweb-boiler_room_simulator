'''
@author: admin
'''

import can


class Message(object):
	'''
	classdocs
	'''


	def __init__(self, programType, programId, functionId, request, data):
		'''
		Constructor
		'''
		self.programId   = programId
		self.programType = programType
		self.functionId  = functionId
		self.request     = request
		self.data        = data
	
	def generateHeader(self):
		if self.request:
			flag = 0x00
		else:
			flag = 0x10

		byte0 = self.programType
		byte1 = self.programId
		byte2 = self.functionId
		byte3 = flag

		header = (
			(byte0 <<  0) |
			(byte1 <<  8) |
			(byte2 << 16) |
			(byte3 << 24))

		return header

	def send(self):
		header = self.generateHeader()

		
		msg = can.Message(
			arbitration_id=header,
			data=self.data,
			is_extended_id=True
		)

		#bus config loaded from ~/can.conf file
		#if you don't have it you should make one
		#https://python-can.readthedocs.io/en/stable/configuration.html
		with can.Bus() as bus:
			bus.send(msg)
			
			
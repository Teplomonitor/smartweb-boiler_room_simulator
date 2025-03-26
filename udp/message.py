'''

@author: admin
'''

import can
import struct

BRIDGE_SIGNATURE = 0x66AB

HEADER_SIZE = 4
BODY_SIZE   = 20
PACKET_SIZE = HEADER_SIZE + BODY_SIZE

BridgeAction = {
	'SCAN' : 0,
	'SEND_CAN' : 1,
}

HEADER_STRUCT = 'hBc'
BODY_STRUCT   = 'I??Bx8sI'


def udp_to_can(data, addr = None):
	offset = 0
	data_size = len(data)
	
	messages = []
	
	while True:
		if (offset + PACKET_SIZE) > data_size:
			return messages
		
		header = struct.unpack(HEADER_STRUCT, data[offset :(offset + HEADER_SIZE)])
		signature = header[0]
		if len(data) < PACKET_SIZE:
			print('Wrong packet format!')
			return messages
		
		if signature == BRIDGE_SIGNATURE:
			print('Ok!')
		else:
			print('Wrong signature!')
			return messages
		
		action = header[1]
		if action == BridgeAction['SEND_CAN']:
			body = struct.unpack(BODY_STRUCT, data[(offset + HEADER_SIZE) : (offset + PACKET_SIZE)])
			msg = can.Message(
				arbitration_id  = body[0],
				is_remote_frame = body[1],
				is_extended_id  = body[2],
				dlc             = body[3],
				data            = body[4],
			)
			messages.append(msg)
		
		offset = offset + PACKET_SIZE
	
	return messages
	
def can_to_udp(msg):
	signature    = BRIDGE_SIGNATURE
	action       = BridgeAction['SEND_CAN']
	reserve      = b'\x00'
	source       = 0
	
	header       = struct.pack(HEADER_STRUCT,
							signature,
							action,
							reserve)
	
	body         = struct.pack(BODY_STRUCT,
							msg.arbitration_id,
							msg.is_remote_frame,
							msg.is_extended_id,
							msg.dlc,
							msg.data,
							source)
	
	udp_msg = struct.pack('4s20s',
						header,
						body)
	return udp_msg

	
	
	
	
	
	
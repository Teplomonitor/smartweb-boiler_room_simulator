'''

@author: admin
'''

import can
import struct

BRIDGE_SIGNATURE = 0x66ab

HEADER_SIZE = 4
BODY_SIZE   = 20
PACKET_SIZE = HEADER_SIZE + BODY_SIZE

SCAN_PACKET_DATA_SIZE = 16
SCAN_PACKET_SIZE = HEADER_SIZE + SCAN_PACKET_DATA_SIZE

BridgeAction = {
	'SCAN' : 0,
	'SEND_CAN' : 1,
}

HEADER_STRUCT = 'hBc'
BODY_STRUCT   = '=I??B8sIx'

BODY_STRUCT_SCAN = '16s'

def check_header(data):
	header = struct.unpack(HEADER_STRUCT, data)
	signature = header[0]

	if signature == BRIDGE_SIGNATURE:
		pass
	else:
		print('Wrong signature!')
		return None
	
	return header[1]
	

def make_header(action):
	signature    = BRIDGE_SIGNATURE
	reserve      = b'\x00'
	
	header       = struct.pack(HEADER_STRUCT,
							signature,
							action,
							reserve)
	return header


def udp_to_can(data):
	offset = 0
	data_size = len(data)
	
	messages = []
	
	while True:
		if (offset + PACKET_SIZE) > data_size:
			return messages
		
		action = check_header(data[offset :(offset + HEADER_SIZE)])
		
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
		else:
			return messages
		
		offset = offset + PACKET_SIZE
	
	return messages
	
def can_to_udp(msg):
	source       = 0
	header       = make_header(BridgeAction['SEND_CAN'])
	
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

	

def get_body(data):
	return data[HEADER_SIZE:]

def get_scan_id(data):
	return data[HEADER_SIZE:SCAN_PACKET_SIZE]

def udp_msg_is_scan(data):
	action = check_header(data[:HEADER_SIZE])
	
	if action == BridgeAction['SCAN']:
		if len(data) >= SCAN_PACKET_SIZE:
			dataLoggerId = struct.unpack(BODY_STRUCT_SCAN, data[HEADER_SIZE: SCAN_PACKET_SIZE])
#			print(dataLoggerId)
		else:
			print('small body?')
		
		return True
	else:
		return False
	
def make_scan_message(dataLoggerId):
	
	header = make_header(BridgeAction['SCAN'])
	
	array = bytearray(header)
	array.extend(dataLoggerId)
	
#	print(f'make udp scan msg {array}')
	
	return array

	
	
	
	
'''
Created on 24 мар. 2025 г.

@author: admin
'''
from os.path import dirname, basename, isfile, join
import glob

import uuid
import socket
import can
import struct
import time
import threading


BRIDGE_SIGNATURE = 0x66ab
BRIDGE_PORT = 31987

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



def make_header(action):
	signature    = BRIDGE_SIGNATURE
	reserve      = b'\x00'
	
	header       = struct.pack(HEADER_STRUCT,
							signature,
							action,
							reserve)
	return header

def get_body(data):
	return data[HEADER_SIZE:]

def get_scan_id(data):
	return data[HEADER_SIZE:SCAN_PACKET_SIZE]

def check_header(data):
	header = struct.unpack(HEADER_STRUCT, data)
	signature = header[0]

	if signature == BRIDGE_SIGNATURE:
		print('Ok!')
	else:
		print('Wrong signature!')
		return None
	
	return header[1]
	
def udp_msg_is_scan(data):
	action = check_header(data[:HEADER_SIZE])
	
	if action == BridgeAction['SCAN']:
		if len(data) >= SCAN_PACKET_SIZE:
			dataLoggerId = struct.unpack(BODY_STRUCT_SCAN, data[HEADER_SIZE: SCAN_PACKET_SIZE])
			print(dataLoggerId)
		else:
			print('small body?')
		
		return True
	else:
		return False
	
		
		
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

def scan_to_udp(dataLoggerId):
	header = make_header(BridgeAction['SCAN'])
	
	array = bytearray(header)
	array.extend(dataLoggerId)
	
	return array

def send_broadcast_udp_packet(data, port):
	interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
	allips = [ip[-1][0] for ip in interfaces]
	
	for ip in allips:
		print(f'sending on {ip}')
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		sock.bind((ip,0))
		sock.sendto(data, ("255.255.255.255", port))
		sock.close()



ip_list      = {}
self_ip_list = []

SELF_ID = uuid.uuid4()
self_id_bytes = SELF_ID.bytes
self_id_bytes = bytearray(self_id_bytes[:SCAN_PACKET_DATA_SIZE])
self_id_bytes[SCAN_PACKET_DATA_SIZE-1] = 0;

def update_ip_list(data, addr):
	body = get_scan_id(data)
	ip   = addr[0]
	if body == self_id_bytes:
		self_ip_list.append(ip)
		print(f'add self ip {ip}')
	else:
		now = time.time()
		ip_list[ip] = now
		print(f'update {ip}')
		
		timeout = 10*60
		
		for ip in ip_list:
			if now - ip_list[ip] > timeout:
				print(f'delete {ip}')
				del ip_list[ip]

class udp_listen_thread(threading.Thread):
	
	def __init__(self, thread_name, thread_ID, port):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._port       = port
		self._sock       = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
		ip_any = '0.0.0.0'
		ip_addr = ip_any
		
		self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self._sock.bind((ip_addr, self._port))


	def run(self):
		while True:
			data, addr = self._sock.recvfrom(1024)
			
			if addr[0] in self_ip_list:
				print(f'skip {addr}')
				continue
			else:
				print(f'recv{data} from {addr}')

			if udp_msg_is_scan(data):
				update_ip_list(data, addr)
				continue
			
def getPresetsList(presetId):
	regex = join(dirname(__file__), 'presets','list', "*.py")
	moduleId = 'presets.list.%s' % presetId
	print(regex)
	print(moduleId)
	modules = glob.glob(regex)
	__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
	
	print(__all__)
	
	if presetId in __all__:
		preset_module = __import__(moduleId, fromlist=["presets.list"])

		return preset_module.getPresetsList()
	print('shit')
	return None


def main():
	getPresetsList('default')
	
	return
	
	msg = can.Message(
		arbitration_id  = 0x12131415,
		is_remote_frame = False,
		is_extended_id  = True,
		dlc             = 8,
		data            = b'\x01\x02\x03\x04\x05\x06\x07\x08',
	)
	udp_msg = can_to_udp(msg)
	
	print(udp_msg)
	
	messages = bytearray([])
	messages.extend(udp_msg)
	messages.extend(udp_msg)
	messages.extend(udp_msg)
	
	print(bytes(messages))
	print(len(messages))
	
	
	can_messages = udp_to_can(messages)
	for can_msg in can_messages:
		print(can_msg)
	
	scan_msg = scan_to_udp(self_id_bytes)
	
	print(scan_msg)
	
	if udp_msg_is_scan(scan_msg):
		print('msg is scan')
		
	thread1 = udp_listen_thread("udp_test", 123, BRIDGE_PORT)
	thread1.daemon = True
	thread1.start()
	
	while True:
		time.sleep(5)
		send_broadcast_udp_packet(scan_msg, BRIDGE_PORT)
	
	
	
if __name__ == '__main__':
	main()
	
	
	
	
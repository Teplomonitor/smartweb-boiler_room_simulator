'''
@author: admin
'''

import uuid
import time
import threading
import socket
from udp.message import udp_to_can, can_to_udp, make_scan_message, udp_msg_is_scan, get_scan_id
from smartnet.message import createBus as createBus

can_udp_bus = createBus()


SCAN_PACKET_DATA_SIZE = 16

ip_list      = {}
self_ip_list = []

SELF_ID = uuid.uuid4()
self_id_bytes = SELF_ID.bytes
self_id_bytes = bytearray(self_id_bytes[:SCAN_PACKET_DATA_SIZE])
self_id_bytes[SCAN_PACKET_DATA_SIZE-1] = 0;

DATA_PACKET_SIZE = 24


def update_ip_list(data, addr):
	body = get_scan_id(data)
	ip   = addr[0]
	
#	print(f'recv udp scan msg {data}')
	
#	print(f'compare {body} and {self_id_bytes}')
	
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

udp_messages_to_send = bytearray([])

def get_send_queue():
	return udp_messages_to_send
	
def clear_send_queue():
#	print('udp clear send queue')
	udp_messages_to_send.clear()

def append_can_udp_message(msg):
#	print('udp add msg to queue')
	udp_msg = can_to_udp(msg)
	udp_messages_to_send.extend(udp_msg)

def send_broadcast_udp_packet(data, port):
	interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
	allips = [ip[-1][0] for ip in interfaces]
	
	for ip in allips:
#		print(f'sending on {ip}')
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		sock.bind((ip,0))
		sock.sendto(data, ("255.255.255.255", port))
		sock.close()

def make_rand_delay(queue_size):
	rand_delay = queue_size/100
	if rand_delay > 0.2:
		rand_delay = 0.2
	
	dt = 0.3 - rand_delay
	return dt

class can_thread(threading.Thread):
	def __init__(self, thread_name, thread_ID, port):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._port       = port
		self._canbus     = can_udp_bus
		self._send_can_time = time.time()
		self._sock       = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
		
	def sendUdpPacket(self, data, udp_ip, udp_port):
#		print(f'send udp packet {data} to {udp_ip}')
		self._sock.sendto(data, (udp_ip, udp_port))


	def run(self):
		while True:
			now = time.time()
			
			messages = get_send_queue()
			queue_size = len(messages)
			dt = make_rand_delay(queue_size)
			
			message = self._canbus.recv(dt)
			
			if message:
#				print(f'udp_tx {message}')
				append_can_udp_message(message)
			
			if ((now - self._send_can_time) > dt) or (queue_size > 10*DATA_PACKET_SIZE):
				if queue_size:
					self._send_can_time = now
#					print(f'udp_tx data {queue_size}')
					for ip in ip_list:
						self.sendUdpPacket(bytes(messages), ip, self._port)
						
					clear_send_queue()
				

class udp_listen_thread(threading.Thread):
	def __init__(self, thread_name, thread_ID, port):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._port       = port
		self._sock       = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._canbus     = can_udp_bus
		self._scan_msg   = make_scan_message(self_id_bytes)
		self._send_scan_time = time.time() - 100
		
		ip_any = '0.0.0.0'

		ip_addr = ip_any
		
		self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self._sock.bind((ip_addr, self._port))
		self._messages = []

	def clear_buffer(self):
		try:
			while self._sock.recv(1024): pass
		except:
			pass
	
	def run(self):
		while True:
			now = time.time()
			
			if now - self._send_scan_time > 60:
				self._send_scan_time = now
				send_broadcast_udp_packet(self._scan_msg, self._port)
			
			data, addr = self._sock.recvfrom(1024)
			
			if addr[0] in self_ip_list:
#				print(f'skip {addr}')
				continue
			else:
#				print(f'recv{data} from {addr}')
				pass
				
			if udp_msg_is_scan(data):
				self._send_scan_time = now
				update_ip_list(data, addr)
				send_broadcast_udp_packet(self._scan_msg, self._port)
				continue
			
			if len(ip_list) == 0:
				continue
			
			messages = udp_to_can(data)
			
			for msg in messages:
#				print(f'udp_rx {msg}')
				self._canbus.send(msg)
			
			
'''
@author: admin
'''

import time
import threading
import socket
from udp.message import can_to_udp, udp_to_can
from smartnet.message import createBus as createBus

ip_list = []
self_ip_list = []

udp_messages_to_send = bytes([])

def get_send_queue():
	return udp_messages_to_send
	
def clear_send_queue():
	udp_messages_to_send = bytes([])


def send_can_to_udp(self, msg):
	data = can_to_udp(msg)
	udp_messages_to_send.extend(data)
		
class udp_send_thread(threading.Thread):
	def __init__(self, thread_name, thread_ID, port):
		threading.Thread.__init__(self)
		self.thread_name = thread_name
		self.thread_ID   = thread_ID
		self._port       = port
		
	def sendUdpPacket(self, data, udp_ip, udp_port):
		self._sock.sendto(data, (udp_ip, udp_port))

	def run(self):
		while True:
			time.sleep(0.3)
			messages = get_send_queue()
			if len(messages):
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
		self._canbus     = createBus
		
		ip_any = '0.0.0.0'

		ip_addr = ip_any
		
		self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self._sock.bind((ip_addr, self._port))
		self._messages = []


	def run(self):
		while True:
			data, addr = self._sock.recvfrom(1024)

			messages = udp_to_can(data, addr)
			
			for msg in messages:
				msg.send(bus = self._canbus)
			
			
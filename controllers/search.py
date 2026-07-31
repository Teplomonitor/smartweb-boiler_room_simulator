'''
Created on 4 июл. 2025 г.

@author: admin
'''

import smartnet.message as snm
import smartnet.constants as snc
import functions.timeOnDelay as delay

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error

def messageIsImHere():
	return snm.Message(
		snc.ProgramType.CONTROLLER, None,
		snc.ControllerFunction['I_AM_HERE'], 
		snc.requestFlag['RESPONSE'])


def findOnlineController(searchingControllerId):
	if searchingControllerId:
		print_log(f'Searching controller {searchingControllerId}')
	else:
		print_log(f'Searching controller')
	
	msg = snm.Message()
	timeout = delay.TimeOnDelay()
	
	while not timeout.get(True, 3*60):
		result = msg.recv(messageIsImHere(), 130)
		if result:
			controllerId   = result.getProgramId()
			controllerType = result.get_data()[0]
			
			if searchingControllerId != 0:
				if controllerId != searchingControllerId:
					print_log(f'skip controller {controllerId}')
					continue
			
			print_log('Controller %d found' %(controllerId))
			
			if controllerType == snc.ControllerType['SWK_1']:
				print_log('skip extension block')
				continue
			
			if controllerType == snc.ControllerType['VIRTUAL']:
				print_log('skip virtual controller')
				continue
			
			return controllerId
		else:
			return None
	
	print_error('Searching controller timeout')
	return None	

'''
Created on 4 июл. 2025 г.

@author: admin
'''

import smartnet.message as snm
import smartnet.constants as snc
import functions.timeOnDelay as delay

from consoleLog import printLog   as printLog
from consoleLog import printError as printError

def messageIsImHere():
	return snm.Message(
		snc.ProgramType['CONTROLLER'], None, 
		snc.ControllerFunction['I_AM_HERE'], 
		snc.requestFlag['RESPONSE'])


def findOnlineController(searchingControllerId):
	if searchingControllerId:
		printLog(f'Searching controller {searchingControllerId}')
	else:
		printLog(f'Searching controller')
	
	msg = snm.Message()
	timeout = delay.TimeOnDelay()
	
	while not timeout.Get(True, 3*60):
		result = msg.recv(messageIsImHere(), 130)
		if result:
			controllerId   = result.getProgramId()
			controllerType = result.getData()[0]
			
			if searchingControllerId != 0:
				if controllerId != searchingControllerId:
					printLog(f'skip controller {controllerId}')
					continue
			
			printLog('Controller %d found' %(controllerId))
			
			if controllerType == snc.ControllerType['SWK_1']:
				printLog('skip extension block')
				continue
			
			if controllerType == snc.ControllerType['VIRTUAL']:
				printLog('skip virtual controller')
				continue
			
			return controllerId
		else:
			return None
	
	printError('Searching controller timeout')
	return None	

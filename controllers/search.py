'''
Created on 4 июл. 2025 г.

@author: admin
'''

import smartnet.message as snm
import smartnet.constants as snc

from consoleLog import printLog   as printLog

def messageIsImHere():
	return snm.Message(
		snc.ProgramType['CONTROLLER'], None, 
		snc.ControllerFunction['I_AM_HERE'], 
		snc.requestFlag['RESPONSE'])


def findOnlineController():
	printLog('Searching controller')
	msg = snm.Message()

	i = 0
	while i < 3:
		result = msg.recv(messageIsImHere(), 130)
		if result:
			controllerId   = result.getProgramId()
			controllerType = result.getData()[0]
			
			printLog('Controller %d found' %(controllerId))
			
			if controllerType == snc.ControllerType['SWK_1']:
				printLog('skip extension block')
				i += 1
				continue
			
			return controllerId
		else:
			return None

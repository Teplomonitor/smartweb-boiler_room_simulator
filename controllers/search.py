'''
Created on 4 июл. 2025 г.

@author: admin
'''

from smartnet.message import Message as smartnetMessage
import smartnet.constants as snc

from consoleLog import printLog   as printLog
from consoleLog import printError as printError

def messageIsImHere():
	return smartnetMessage(
		snc.ProgramType['CONTROLLER'], None, 
		snc.ControllerFunction['I_AM_HERE'], 
		snc.requestFlag['RESPONSE'])


def findOnlineController():
	printLog('Searching controller')
	msg = smartnetMessage()

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

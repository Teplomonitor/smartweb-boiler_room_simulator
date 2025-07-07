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
	result = msg.recv(messageIsImHere(), 130)
	if result:
		controllerId = result.getProgramId()
		printLog('Controller %d found' %(controllerId))
		return controllerId
	else:
		return None

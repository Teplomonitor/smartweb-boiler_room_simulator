'''
@author: admin
'''

gui = None

def initGui(guiThread):
	global gui
	gui = guiThread

def printLog(log_str):
	print(log_str)
	global gui
	if gui:
		gui.printConsoleText(log_str)

def printError(log_str):
	print(log_str)
	global gui
	if gui:
		gui.printConsoleText(log_str)
		
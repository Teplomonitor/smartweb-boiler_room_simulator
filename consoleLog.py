'''
@author: admin
'''

import datetime

gui = None

def initGui(guiThread):
	global gui
	gui = guiThread

def printLog(log_str):
	dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	
	log_str_with_dt = f'{dt}   {log_str}'
	
	print(log_str_with_dt)
	global gui
	if gui:
#		gui.setTextColor('GREEN')
		gui.printConsoleText(log_str_with_dt)

def printError(log_str):
	dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	
	log_str_with_dt = f'{dt}   {log_str}'
	
	print(log_str_with_dt)
	global gui
	if gui:
#		gui.setTextColor('RED')
		gui.printConsoleText(log_str_with_dt)
		
'''
@author: admin
'''

import datetime
import os
import threading

gui = None
_log_messages = []
_log_lock = threading.Lock()

def init_gui(guiThread):
	global gui
	gui = guiThread

def _print_message(log_str, color):
	dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	log_str_with_dt = f'{dt}   {log_str}'

	with _log_lock:
		_log_messages.append(log_str_with_dt)

	print(log_str_with_dt)
	global gui
	if gui:
		gui.printConsoleText(log_str_with_dt, color)

def print_log(log_str):
	_print_message(log_str, 'GREEN')

def print_error(log_str):
	_print_message(log_str, 'RED')

def save_log(log_dir=None):
	"""Save the console messages collected during the current application run."""
	if log_dir is None:
		log_dir = os.environ.get('BRS_LOG_ROOT', os.path.join(os.getcwd(), 'log'))

	with _log_lock:
		messages = list(_log_messages)

	os.makedirs(log_dir, exist_ok=True)
	timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
	log_path = os.path.join(log_dir, f'console_{timestamp}.txt')
	with open(log_path, 'w', encoding='utf-8', newline='') as log_file:
		log_file.write('\n'.join(messages))
		if messages:
			log_file.write('\n')

	return log_path
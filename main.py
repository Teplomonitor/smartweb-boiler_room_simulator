#!/usr/bin/env python3
# encoding: utf-8
'''
 -- shortdesc

 is a description

It defines classes_and_methods

@author:     user_name

@copyright:  2025 organization_name. All rights reserved.

@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

import sys
import os

import time

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

import presets.preset
from smartnet.message import Message as smartnetMessage

from controllers.controller    import findOnlineController   as findOnlineController
from controllers.controller    import Controller             as Controller
from controllers.controller_io import initVirtualControllers as initVirtualControllers
from scenario.scenario         import ScenarioThread         as ScenarioThread
from simulator.simulator       import initIoSimulator        as initIoSimulator

import debug
from udp.udp import initUdpBridge as initUdpBridge

def mock_missing(name):
	def init(self, *args, **kwargs):
		raise ImportError(
			f'The class {name} you tried to call is not importable; '
			f'this is likely due to it not being installed.')
	return type(name, (), {'__init__': init})

try:
	import gui.frame as guiFrameThread
except:
	guiFrameTherad = mock_missing('guiFrameTherad')

__all__ = []
__version__ = 0.1
__date__ = '2025-03-04'
__updated__ = '2025-03-04'

DEBUG = 0



guiThread = None

def printLog(log_str):
	print(log_str)
	if guiThread:
		guiThread.printConsoleText(log_str)

def printError(log_str):
	print(log_str)
	if guiThread:
		guiThread.printConsoleText(log_str)


class CLIError(Exception):
	'''Generic exception to raise and log different fatal errors.'''
	def __init__(self, msg):
		super(CLIError).__init__(type(self))
		self.msg = "E: %s" % msg
	def __str__(self):
		return self.msg
	def __unicode__(self):
		return self.msg

def initArgParser(program_license):
	parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
	parser.add_argument('-d', '--debug'   , action='store_true'                          , help='start debugger that will reply on simulator commands') 
	parser.add_argument(      '--init'    , action='store_true'                          , help='init controller with preset') 
	parser.add_argument('-p', '--preset'  , nargs='?', const='default', default='default', help='select controller config')
	parser.add_argument('-u', '--udp'     , nargs='?', const=31987    , default=0        , help='enable CAN-UDP bridge. Can be value from 0 to 65535. 0 - disable CAN-UDP bridge')
	parser.add_argument(      '--gui'     , action='store_true'                          , help='enable gui window') 
	parser.add_argument('-s', '--scenario', nargs='?', const='default', default='none'   , help='enable automatic scenarion run')
	
	return parser.parse_args()

def initScenario(controller, sim):
	scenarioThread = ScenarioThread(controller, sim)
	scenarioThread.daemon = True
	scenarioThread.start()

def main(argv=None): # IGNORE:C0111
	'''Command line options.'''

	if argv is None:
		argv = sys.argv
	else:
		sys.argv.extend(argv)

	program_name = os.path.basename(sys.argv[0])
	program_version = "v%s" % __version__
	program_build_date = str(__updated__)
	program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
	program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
	program_license = '''%s

	%s
	
	Created by user_name on %s.
	Copyright 2025 organization_name. All rights reserved.

	Licensed under the Apache License 2.0
	http://www.apache.org/licenses/LICENSE-2.0

	Distributed on an "AS IS" basis without warranties
	or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, program_version_message, str(__date__))

	try:
		# Setup argument parser
		args = initArgParser(program_license)
		
		init_controller_with_preset = args.init
		udp_bridge_enable           = int(args.udp)
		preset                      = args.preset
		scenario                    = args.scenario
		
		programList, controllerIoList = presets.preset.getPresetsList(preset)
		
		
		if programList is None:
			print('wrong preset. Exit')
			return 1
		
		if udp_bridge_enable:
			initUdpBridge(udp_bridge_enable)
		
		if args.debug:
			dbgThread = debug.debug_thread()
			
		controllerId = findOnlineController()
		
		if controllerId is None:
			print('controller not found. Exit')
			return 1
		
		if args.gui:
			guiThread = guiFrameThread.guiThread("GUI", 666)
		
		controller = Controller(controllerId, init_controller_with_preset, programList, guiThread)
		
		ctrlIo = initVirtualControllers(controllerIoList)
		
		sim = initIoSimulator(controller, ctrlIo)
		
		if scenario != 'none':
			initScenario(controller, sim)
		
		if guiThread:
			guiThread.run()
		else:
			while True:
				time.sleep(1)
		
		smartnetMessage.exit()
		
		return 0
	
	except KeyboardInterrupt:
		### handle keyboard interrupt ###
		smartnetMessage.exit()
		print('exit')
		return 0
	except Exception as e:
		smartnetMessage.exit()
		
		if DEBUG:
			raise(e)
		indent = len(program_name) * " "
		sys.stderr.write(program_name + ": " + repr(e) + "\n")
		sys.stderr.write(indent + "  for help use --help")
		return 2

if __name__ == "__main__":
	if DEBUG:
		sys.argv.append("-d")
		
	sys.exit(main())
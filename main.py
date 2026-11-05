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

if sys.stdout is None:
	sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
	sys.stderr = open(os.devnull, 'w')

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter


import mainThread
import consoleLog
from application import Application


__all__ = []
__version__ = 0.1
__date__ = '2025-03-04'
__updated__ = '2025-03-04'

DEBUG = 0


class CLIError(Exception):
	'''Generic exception to raise and log different fatal errors.'''
	def __init__(self, msg):
		super(CLIError).__init__(type(self))
		self.msg = "E: %s" % msg
	def __str__(self):
		return self.msg
	def __unicode__(self):
		return self.msg

def initArgParser(program_license, argv=None):
	parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
	parser.add_argument('-d', '--debug'   , action='store_true'                          , help='start debugger that will reply on simulator commands')
	parser.add_argument('-p', '--profile' , nargs='?', const='main'   , default='main'   , help='select program profile')
	parser.add_argument('-u', '--udp'     , nargs='?', const=31987    , default=0        , help='enable CAN-UDP bridge. Can be value from 0 to 65535. 0 - disable CAN-UDP bridge')
	parser.add_argument(      '--console' , action='store_true'                          , help='keep a console window open when using a Windows launch script')
	parser.add_argument(      '--gui'     , action='store_true'       , default=True     , help='enable gui window. [DEPRECATED] GUI always enable by default now. Use --no-gui to switch off GUI')
	parser.add_argument(      '--no-gui'  , action='store_false'      , dest='gui'       , help='disable gui window')
	parser.add_argument(      '--id'      , nargs='?'                 , default=0        , help='select specific controller ID address to control')
	parser.add_argument('-s', '--scenario', nargs='?', const='all'    , default='none'   , help='enable automatic scenarion run')
	parser.add_argument(      '--scenarios', nargs='+', metavar='PATH', help='run only these scenario files in parallel mode')
	parser.add_argument('-c', '--can'     , nargs='?', const='default', default='none'   , help='select CANBus config')
	parser.add_argument(      '--can-ports', nargs='+', metavar='CONTEXT', help='run scenarios across distinct CAN config contexts (requires --no-gui)')
	parser.add_argument(      '--udp-ports', nargs='+', metavar='PORT', help='run scenarios across distinct controller UDP bridge ports (requires --no-gui)')
	parser.add_argument(      '--can-worker', action='store_true', help='internal parallel CAN worker mode')
	parser.add_argument(      '--can-gui-child', action='store_true', help='internal parallel CAN GUI coordinator mode')
	parser.add_argument(      '--preset'  , nargs='?'                 , default=None     , help='load specific preset on controller startup')
	parser.add_argument('--web-url', help='embedded controller origin, e.g. http://192.168.1.50; enables web tests')
	parser.add_argument('--web-login', default='admin', help='embedded web login (default: admin)')
	parser.add_argument('--web-password-env', default='BRS_WEB_PASSWORD', help='password environment variable (fallback: admin)')
	parser.add_argument('--web-timeout', type=float, default=10.0, help='HTTP timeout in seconds (default: 10)')
	parser.add_argument('--web-bench', help='dedicated binding bench JSON profile')
	parser.add_argument('--confirm-web-bench', action='store_true', help='confirm destructive tests on a dedicated bench')
	args = parser.parse_args(argv)
	if args.web_bench:
		from pathlib import Path
		from web_binding_bench import ROOT, discover_scenarios, load_settings, validate_settings
		try:
			bench = validate_settings(load_settings(args.web_bench), require_ready=True)
		except (ValueError, OSError, UnicodeError) as error:
			parser.error(str(error))
		if args.preset or args.gui or args.debug or args.can_ports or args.udp_ports or args.can_worker or args.can_gui_child or args.scenarios:
			parser.error('Bench profiles require --no-gui, no startup preset, no debug or parallel workers')
		if args.scenario != 'none' and not args.confirm_web_bench:
			parser.error('Bench scenarios require --confirm-web-bench')
		if args.scenario != 'none' and Path(args.scenario).resolve() not in {
				(ROOT / item['path']).resolve() for item in discover_scenarios()}:
			parser.error('Only an explicit implemented binding scenario path is allowed with --web-bench')
		if int(args.id) not in (0, bench['devices']['dut_controller']):
			parser.error('--id conflicts with the bench DUT ID')
		args.id = bench['devices']['dut_controller']
		args.web_url = bench['web']['url']
		args.web_login = bench['web']['login']
		args.web_timeout = bench['web']['timeout']
		args.can = bench['transport']['can_context'] if bench['transport']['mode'] == 'can' else 'virtual'
		args.udp = bench['transport']['udp_port'] if bench['transport']['mode'] == 'udp' else 0
		args.bench_settings = bench
	if args.web_url:
		if args.can_ports or args.udp_ports or args.can_worker or args.can_gui_child:
			parser.error('Web tests currently support only a single controller session')
		if args.debug or not 1 <= int(args.id) <= 255:
			parser.error('Web tests require --id 1..255 and do not support --debug')
	return args

def getProgramLicense():
	program_version = "v%s" % __version__
	program_build_date = str(__updated__)
	program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
	program_shortdesc = __doc__.split("\n")[1]
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
	return program_license

def loadPreset(preset, scenario=False):
	t = mainThread.MainThread()
	t.loadPreset(preset, scenario=scenario)
	

def saveProgramPlots():
	t = mainThread.MainThread()
	t.saveProgramPlots()

def loadPresetDone():
	t = mainThread.MainThread()
	return t.loadPresetDone()

def load_preset_succeeded():
	return mainThread.MainThread().load_preset_succeeded()

def get_preset_error():
	return mainThread.MainThread().get_preset_error()

def initMainThread(args):
	mainThread.MainThread(args)

def MainStop():
	mainThread.MainStop()
	
def main(argv=None): # IGNORE:C0111
	'''Command line options.'''
	
	program_name = os.path.basename(sys.argv[0])
	application = None
	exit_code = 0

	try:
		program_license = getProgramLicense()
		# Setup argument parser
		args = initArgParser(program_license, argv)
		if args.scenarios and not (args.can_ports or args.udp_ports):
			raise ValueError('--scenarios requires --can-ports or --udp-ports')
		if args.can_ports or args.udp_ports:
			from parallel_can import run_coordinator
			return run_coordinator(args)
		if args.can_worker:
			from parallel_can import run_worker
			if args.gui or args.scenario != 'none' or (args.udp and args.can != 'virtual'):
				raise ValueError('Parallel worker requires --no-gui; UDP workers require --can virtual')
			return run_worker(args)
		application = Application(args)
		application.start()
		if application.gui:
			application.gui.run()
		else:
			application.stop_event.wait()
	
	except KeyboardInterrupt:
		### handle keyboard interrupt ###
		consoleLog.print_log('exit')
	
	except Exception as e:
		if DEBUG:
			raise(e)
		indent = len(program_name) * " "
		sys.stderr.write(program_name + ": " + repr(e) + "\n")
		sys.stderr.write(indent + "  for help use --help")
		exit_code = 2
	finally:
		if application:
			if not application.shutdown():
				exit_code = 2
			if application.worker and application.worker.error:
				exit_code = 2
	return exit_code

if __name__ == "__main__":
	if DEBUG:
		sys.argv.append("-d")
		
	sys.exit(main())

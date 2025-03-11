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
 

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from smartnet.message import Message as smartnetMessage
import smartnet.constants as snc
from controllers.controller import Controller as Controller
from simulator.simulator import Simulator as Simulator

import debug


__all__ = []
__version__ = 0.1
__date__ = '2025-03-04'
__updated__ = '2025-03-04'

DEBUG = 1
TESTRUN = 0
PROFILE = 0

class CLIError(Exception):
	'''Generic exception to raise and log different fatal errors.'''
	def __init__(self, msg):
		super(CLIError).__init__(type(self))
		self.msg = "E: %s" % msg
	def __str__(self):
		return self.msg
	def __unicode__(self):
		return self.msg





def messageIsImHere():
	return smartnetMessage(
		snc.ProgramType['CONTROLLER'], None, 
		snc.ControllerFunction['I_AM_HERE'], 
		snc.requestFlag['RESPONSE'])


def findOnlineController():
	result = smartnetMessage.recv(15, messageIsImHere())
	if result:
		return result.getProgramId()
	else:
		return None

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

	Created by user_name on %s.
	Copyright 2025 organization_name. All rights reserved.

	Licensed under the Apache License 2.0
	http://www.apache.org/licenses/LICENSE-2.0

	Distributed on an "AS IS" basis without warranties
	or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

	try:
		# Setup argument parser
#		parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)

		# Process arguments
#		args = parser.parse_args()

		dbgThread = debug.debug_thread()

		print('Searching controller')
		controllerId = findOnlineController()

		if controllerId is None:
			print("shit")
			return 1
		
		print('Controller %d found' %(controllerId))
		controller = Controller(controllerId)
		simulator  = Simulator(controller)

		simulator.run()
		return 0

	except KeyboardInterrupt:
		### handle keyboard interrupt ###
		smartnetMessage.exit()
		print('exit')
		return 0
	except Exception as e:
		smartnetMessage.exit()

		if DEBUG or TESTRUN:
			raise(e)
		indent = len(program_name) * " "
		sys.stderr.write(program_name + ": " + repr(e) + "\n")
		sys.stderr.write(indent + "  for help use --help")
		return 2

if __name__ == "__main__":
	if DEBUG:
		sys.argv.append("-h")
		sys.argv.append("-v")
		sys.argv.append("-r")
	if TESTRUN:
		import doctest
		doctest.testmod()
	if PROFILE:
		import cProfile
		import pstats
		profile_filename = '_profile.txt'
		cProfile.run('main()', profile_filename)
		statsfile = open("profile_stats.txt", "wb")
		p = pstats.Stats(profile_filename, stream=statsfile)
		stats = p.strip_dirs().sort_stats('cumulative')
		stats.print_stats()
		statsfile.close()
		sys.exit(0)
	sys.exit(main())
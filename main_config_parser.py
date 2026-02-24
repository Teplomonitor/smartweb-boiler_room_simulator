



import sys
import config_parser.gui as guiFrameThread

def main(argv=None):
	guiThread = guiFrameThread.guiThread()

	# should run in main loop
	if guiThread:
		guiThread.run()


if __name__ == "__main__":
	sys.exit(main())
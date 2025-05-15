
import time

class PeriodicTrigger(object):
	def __init__(self):
		self._previousStateSetup = time.time()

	def Get(self, period):
		now = time.time()
		dt  = now - self._previousStateSetup
		
		if (dt > period):
			self._previousStateSetup = now;
			return True
		
		return False

	def TimerReset(self):
		self._previousStateSetup = time.time()


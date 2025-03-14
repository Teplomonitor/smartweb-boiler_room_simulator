
import time

class PeriodPulse(object):
	def __init__(self):
		self._state = False
		self._previousStateSetup = time.time()

	def Get(self, onPeriod, offPeriod):
		if onPeriod == 0:
			return False
		
		if offPeriod == 0:
			return True
		
		now = time.time()
		dt  = now - self._previousStateSetup
		
		if ((	(self._state == True ) and (dt > onPeriod)) or
			   ((self._state == False) and (dt > offPeriod))):
			self._previousStateSetup = now;
			self._state = not self._state;
		
		return self._state;

	def TimerReset(self):
		self._previousStateSetup = time.time()
		self._state = False


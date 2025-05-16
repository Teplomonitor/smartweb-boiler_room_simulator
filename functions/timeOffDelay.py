
import time

class TimeOffDelay(object):
	def __init__(self):
		self._state = False
		self._previousStateSetup = time.time()

	def Get(self, value, offDelay):
		if offDelay == 0:
			self._state = value
			return self._state
		
		now = time.time()
		
		if value:
			self._previousStateSetup = now
			self._state = True
			return self._state
		
		dt = now - self._previousStateSetup
		
		if dt >= offDelay:
			self._previousStateSetup = now - offDelay
			self._state = False
			return self._state
		
		self._state = True
		
		return self._state

	def TimerReset(self):
		self._previousStateSetup = time.time()
		self._state = False


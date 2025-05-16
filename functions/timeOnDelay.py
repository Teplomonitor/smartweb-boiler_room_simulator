
import time

class TimeOnDelay(object):
	def __init__(self):
		self._state = False
		self._previousStateSetup = time.time()

	def Get(self, value, onDelay):
		if onDelay == 0:
			self._state = value
			return self._state
		
		now = time.time()
		
		if not value:
			self._previousStateSetup = now
			return False
		
		dt = now - self._previousStateSetup
		
		if dt >= onDelay:
			self._previousStateSetup = now - onDelay
			self._state = True
			return self._state
		
		self._state = False
		
		return self._state

	def TimerReset(self):
		self._previousStateSetup = time.time()
		self._state = False



import time

class TimeOnDelay(object):
	def __init__(self):
		self._out         = False
		self._onTime      = time.time()
		self._elapsedTime = 0
		self._firstStart  = False

	def Get(self, value, onDelay, manualReset = False):
		if (self._firstStart):
			self._firstStart = False
			self.TimerReset()
			
		if value:
			self._out = self.GetCropedElapsedTime() >= onDelay
		else:
			self._out = False
			now = time.time()
	
			if manualReset:
				self._onTime = now - self._elapsedTime
			else:
				self._elapsedTime = 0
				self._onTime = now
			
		return self._out
	
	def GetCropedElapsedTime(self):
		if not self._out:
			self._elapsedTime = time.time() - self._onTime

		return self._elapsedTime
	
	def TimerReset(self):
		self._out         = False
		self._elapsedTime = 0
		self._onTime      = time.time()

